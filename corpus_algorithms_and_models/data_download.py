from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed, wait, TimeoutError
from convokit import Corpus, download

import os
import re
import pickle
import multiprocessing
import logging

logging.basicConfig(
        filename="./corpus_algorithms_and_models/corpus_downloader.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def load_list_from_file(filename):
    """Load and sanitize the subreddit list from a file."""
    logging.info(f"Loading file: {filename}")

    if not os.path.exists(filename):
        logging.error(f"File not found: {filename}")
        return []

    try:
        with open(filename, 'r') as file:
            subreddit_list = [
                stripped_line for line in file
                if (stripped_line := line.strip()) and not re.search(r'[<>:"/\\|?*]', stripped_line)
            ]
        logging.info(f"Loaded subreddits: {len(subreddit_list)}")
        return subreddit_list

    except Exception as e:
        logging.error(f"Error loading file {filename}: {e}")
        return []
    
def chunked(iterable, size):
    """Yield successive chunks of the given size from the iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

def corpus_has_text(corpus, min_conversations=10, min_text_length=1000):
    """Check if a corpus has enough meaningful text."""
    num_conversations = len(corpus.get_conversation_ids())
    total_text_length = sum(len(utterance.text or "") for utterance in corpus.iter_utterances())
    return num_conversations >= min_conversations and total_text_length >= min_text_length

def download_corpus(name, min_conversations=10, min_text_length=1000):
    """Download a single corpus and validate its content."""
    try:
        corpus = Corpus(filename=download(name))
        logging.info(f"Corpus loaded: {name}")
        if corpus_has_text(corpus, min_conversations, min_text_length):
            logging.info(f"Corpus valid: {name}, conversations: {len(corpus.get_conversation_ids())}")
            return corpus
        else:
            logging.warning(f"Corpus invalid: {name}")
    except Exception as e:
        logging.error(f"Download failed: {name}, error: {e}")
    return None

def download_corpora(main_corpus_name, subreddit_names, max_threads=24, min_conversations=10, min_text_length=1000, timeout=600):
    """Download multiple corpora concurrently with a timeout for each download."""
    results = []
    all_names = [main_corpus_name] + subreddit_names

    with ThreadPoolExecutor(max_threads) as executor:
        future_to_name = {executor.submit(download_corpus, name, min_conversations, min_text_length): name for name in all_names}
        
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                corpus = future.result(timeout=timeout)
                if corpus:
                    results.append((name, corpus))
            except TimeoutError:
                logging.warning(f"Timeout: {name}")
            except Exception as e:
                logging.error(f"Error: {name}, {e}")

    logging.info(f"Batch completed: {len(results)} successful, {len(all_names) - len(results)} failed")
    corpus_collection = [corpus for _, corpus in results]
    corpus_names = [name for name, _ in results]
    return corpus_collection, corpus_names

def process_batch(batch, main_corpus_name, max_threads, min_conversations, min_text_length, timeout):
    """Process a single batch of subreddits."""
    logging.info(f"Processing batch: {len(batch)} subreddits")
    corpus_collection, corpus_names = download_corpora(
        main_corpus_name=main_corpus_name,
        subreddit_names=batch,
        max_threads=max_threads,
        min_conversations=min_conversations,
        min_text_length=min_text_length,
        timeout=timeout
    )
    return corpus_collection, corpus_names

def main():
    logging.info("Starting downloader")

    main_corpus_name = "subreddit-corpus"
    subreddit_list = load_list_from_file("./corpus_algorithms_and_models/subreddits.txt")
    if not subreddit_list:
        logging.error("No subreddits loaded. Exiting.")
        return 1
    batch_size = 10000
    max_concurrent_batches = min(4, multiprocessing.cpu_count() // 2)

    logging.info(f"Total subreddits: {len(subreddit_list)}, Batch size: {batch_size}, Concurrent batches: {max_concurrent_batches}")

    batches = list(chunked(subreddit_list, batch_size))
    all_corpus_collection = []
    all_corpus_names = []

    with ProcessPoolExecutor(max_concurrent_batches) as executor:
        future_to_batch = {
            executor.submit(
                process_batch,
                batch,
                main_corpus_name,
                24,
                10,
                1000,
                600
            ): batch_num
            for batch_num, batch in enumerate(batches, start=1)
        }

        for future in as_completed(future_to_batch):
            batch_num = future_to_batch[future]
            try:
                corpus_collection, corpus_names = future.result()
                all_corpus_collection.extend(corpus_collection)
                all_corpus_names.extend(corpus_names)
                logging.info(f"Batch success: {batch_num}")
            except Exception as e:
                logging.error(f"Batch failed: {batch_num}, {e}")
    
    logging.info(f"All batches complete. Saving results.")
    with open("corpora_data.pkl", "wb") as file:
        pickle.dump((all_corpus_collection, all_corpus_names), file)
        logging.info(f"Results saved: corpora_data.pkl")
    return 0

if __name__ == "__main__":
    main()