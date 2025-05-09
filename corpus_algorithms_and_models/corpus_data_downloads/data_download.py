from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed, wait, TimeoutError
import shutil
from convokit import Corpus, download
from multiprocessing import Lock
import os
import re
import pickle
import multiprocessing
import logging
import pandas as pd
import fileinput

logging.basicConfig(
        filename="./corpus_algorithms_and_models/corpus_data_downloads/corpus_download_logs/corpus_downloader_1.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

file_lock = Lock()

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

def clear_directory(name, unzipped_path):
    """Delete all contents of a directory, but keep the directory itself."""
    zipped_path = f"{unzipped_path}.zip"
    try:
        for path in [unzipped_path, zipped_path]:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
    except Exception as e:
        logging.warning(f"Failed to delete {path}: {e}")
    finally:
        # Open the file in in-place mode and remove the line containing the target_line
        with fileinput.FileInput("C:\\Users\\Connor\\.convokit\\saved-corpora\\downloads\\downloaded.txt", inplace=True) as file:
            for line in file:
                # Compare only the first part of the line before $#$
                if line.split('$#$')[0] != name:
                    print(line, end='')  # Print the line (writing it back to the file)

def sanitize_text(text):
    if text is None:
        return ""
    return ''.join(char for char in text if char.isprintable() and ord(char) not in range(0x00, 0x20))

def append_to_csv(data, output_csv="./corpus_algorithms_and_models/corpus_data_downloads/data/master_corpus.csv"):
    """
    Appends data to a CSV file instead of keeping everything in memory.
    """
    df = pd.DataFrame(data)
    df.to_csv(output_csv, mode='a', header=not os.path.exists(output_csv), index=False, encoding="utf-8")

def process_corpus(corpus_name, corpus, output_csv="./corpus_algorithms_and_models/corpus_data_downloads/data/master_corpus.csv"):
    """
    Process a single corpus and append results to CSV to prevent memory overload.
    """
    print(f"Processing corpus: {corpus_name}")
    
    master_data = []
    for conversation in corpus.iter_conversations():
        conv_id = conversation.id
        res_id_counter = 1

        for utterance in conversation.iter_utterances():
            sanitized_answer = sanitize_text(utterance.text)
            master_data.append({
                "corpus_name": corpus_name,
                "conv_id": conv_id,
                "res_id": res_id_counter,
                "question_text": "DUMMY DATA",
                "answer_text": sanitized_answer
            })
            res_id_counter += 1
        
        # Append to CSV after processing each conversation
        if len(master_data) >= 10000:  # Flush after every 10,000 rows to reduce memory use
            append_to_csv(master_data, output_csv)
            master_data.clear()

    # Append any remaining data
    if master_data:
        append_to_csv(master_data, output_csv)

    print(f"Finished processing corpus: {corpus_name}")

def corpus_has_text(corpus, min_conversations=10, min_text_length=1000):
    """Check if a corpus has enough meaningful text."""
    num_conversations = len(corpus.get_conversation_ids())
    total_text_length = sum(len(utterance.text or "") for utterance in corpus.iter_utterances())
    return num_conversations >= min_conversations and total_text_length >= min_text_length

def download_corpus(name, min_conversations=10, min_text_length=1000):
    """Download a single corpus and validate its content."""
    try:
        valid = False
        download_path = download(name)
        corpus = Corpus(filename=download_path)
        logging.info(f"Corpus loaded: {name}")
        if corpus_has_text(corpus, min_conversations, min_text_length):
            valid = True
            logging.info(f"Corpus valid: {name}, conversations: {len(corpus.get_conversation_ids())}")
        else:
            logging.warning(f"Corpus invalid: {name}")
            return None
        
        process_corpus(name, corpus, "./corpus_algorithms_and_models/corpus_data_downloads/data/master_corpus.csv")

    except Exception as e:
        logging.error(f"Download failed: {name}, error: {e}")

    finally:
        # Delete downloaded file if it exists
        if download_path and os.path.isdir(download_path):
            clear_directory(name, download_path)
            logging.info(f"Cleared contents of: {download_path}")

    return corpus if valid else None


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
    logging.basicConfig(
        filename="./corpus_algorithms_and_models/corpus_data_downloads/corpus_download_logs/corpus_downloader_1.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
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
    subreddit_list = load_list_from_file("./corpus_algorithms_and_models/corpus_data_downloads/subreddit_names/subreddits_3.txt")
    if not subreddit_list:
        logging.error("No subreddits loaded. Exiting.")
        return 1
    
    batch_size = 10000
    max_concurrent_batches = 1 # min(4, multiprocessing.cpu_count() // 2)

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
                1,
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