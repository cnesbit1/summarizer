from concurrent.futures import ThreadPoolExecutor, as_completed
from convokit import TextCleaner, Corpus, download
from openpyxl.utils.exceptions import IllegalCharacterError

import pandas as pd
import os
import re

def has_invalid_characters(name):
    return bool(re.search(r'[<>:"/\\|?*]', name))

def sanitize_text(text):
    if text is None:
        return ""
    # Remove non-printable characters and illegal characters
    return ''.join(char for char in text if char.isprintable() and ord(char) not in range(0x00, 0x20))

def load_list_from_file(filename):
    """Load the subreddit list from a file."""
    print(f"Loading subreddit list from {filename}...")
    if not os.path.exists(filename):
        print(f"File {filename} does not exist. Returning an empty list.")
        return []
    
    with open(filename, 'r') as file:
        subreddit_list = [line.strip() for line in file if line.strip()]
    print(f"Loaded {len(subreddit_list)} subreddits.")
    return subreddit_list

def corpus_has_text(corpus, min_conversations=10, min_text_length=1000):
    """Check if a corpus has enough meaningful text."""
    num_conversations = len(corpus.get_conversation_ids())
    total_text_length = sum(len(utterance.text or "") for utterance in corpus.iter_utterances())
    return num_conversations >= min_conversations and total_text_length >= min_text_length

def download_corpus(name, min_conversations=10, min_text_length=1000):
    """Download a single corpus and validate its content."""
    try:
        corpus = Corpus(filename=download(name))
        if corpus_has_text(corpus, min_conversations, min_text_length):
            print(f"Corpus '{name}' downloaded with {len(corpus.get_conversation_ids())} conversations.")
            create_excel_file(corpus, name)
            return corpus
        else:
            print(f"Corpus '{name}' does not meet the required criteria. Skipping...")
    except Exception as e:
        print(f"Error downloading corpus '{name}': {e}")
    return None

def download_corpora_concurrently(main_corpus_name, subreddit_names, max_threads=24, min_conversations=10, min_text_length=1000):
    """Download multiple corpora concurrently using ThreadPoolExecutor."""
    results = []
    all_names = [main_corpus_name] + subreddit_names

    with ThreadPoolExecutor(max_threads) as executor:
        future_to_name = {executor.submit(download_corpus, name, min_conversations, min_text_length): name for name in all_names}
        
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                corpus = future.result()
                if corpus:
                    results.append((name, corpus))
            except Exception as e:
                print(f"Error processing '{name}': {e}")

    print(f"Downloaded {len(results)} corpora out of {len(all_names)} total.")
    corpus_collection = [corpus for _, corpus in results]
    corpus_names = [name for name, _ in results]
    return corpus_collection, corpus_names

def create_excel_file(corpus, corpus_name, output_dir="./concurrent_input_data"):
    """Create an Excel file for a single corpus."""
    print(f"Processing corpus: {corpus_name}")
    
    data = {
        "conv_id": [],
        "res_id": [],
        "question_text": [],
        "answer_text": [],
    }

    excel_path = os.path.join(output_dir, f"{corpus_name}.xlsx")
    if os.path.exists(excel_path):
        print(f"File '{excel_path}' already exists. Skipping...")
        return

    for conversation in corpus.iter_conversations():
        conv_id = conversation.id
        res_id_counter = 1

        for utterance in conversation.iter_utterances():
            # Sanitize question and response fields
            data["conv_id"].append(conv_id)
            data["res_id"].append(res_id_counter)
            sanitized_question = sanitize_text(utterance.text)
            data["question_text"].append(sanitized_question)

            if utterance.reply_to and utterance.reply_to in corpus.get_utterance_ids():
                reply_utterance = corpus.get_utterance(utterance.reply_to)
                sanitized_answer = sanitize_text(reply_utterance.text)
                data["answer_text"].append(sanitized_answer)
            else:
                data["answer_text"].append("N/A")

            res_id_counter += 1

    print(f"Processed {len(data['conv_id'])} responses for '{corpus_name}'.")
    
    df = pd.DataFrame(data)
    
    try:
        print(f"Writing data to Excel file: {excel_path}")
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"Excel file created for '{corpus_name}': {excel_path}")
    except IllegalCharacterError as e:
        print(f"Error writing to Excel for {corpus_name}: {e}")

# def create_excel_files(corpus_collection, corpus_names, output_dir="./concurrent_input_data"):
#     """Create Excel files for all corpora."""
#     print(f"Creating output directory at {output_dir}...")
#     os.makedirs(output_dir, exist_ok=True)
#     print("Output directory is ready.")

#     for i, corpus in enumerate(corpus_collection):
#         create_excel_file(corpus, corpus_names[i], output_dir)

if __name__ == "__main__":
    original_directory = os.getcwd()
    os.chdir("corpus_algorithms_and_models")

    main_corpus_name = "subreddit-corpus"
    subreddit_list = load_list_from_file("./subreddits.txt")
    cleaned_subreddit_list = [subreddit for subreddit in subreddit_list if not has_invalid_characters(subreddit)]

    print("Starting concurrent corpus downloading...")
    corpus_collection, all_corpus_names = download_corpora_concurrently(
        main_corpus_name, 
        cleaned_subreddit_list, 
        max_threads=24,  # Adjust the number of threads
        min_conversations=10,  # Minimum number of conversations
        min_text_length=1000  # Minimum total text length
    )
    print("Concurrent corpus downloading completed.")

    # os.chdir(original_directory)
    # print("Starting Excel file creation process...")
    # create_excel_files(corpus_collection, all_corpus_names)
    # print("Excel file creation process completed.")
