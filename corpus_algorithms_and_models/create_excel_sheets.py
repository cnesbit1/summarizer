from openpyxl.utils.exceptions import IllegalCharacterError
from convokit import Corpus
import os
import pandas as pd
import time

def sanitize_text(text):
    if text is None:
        return ""
    return ''.join(char for char in text if char.isprintable() and ord(char) not in range(0x00, 0x20))

def append_to_csv(data, output_csv="./master_corpus.csv"):
    """
    Appends data to a CSV file instead of keeping everything in memory.
    """
    df = pd.DataFrame(data)
    df.to_csv(output_csv, mode='a', header=not os.path.exists(output_csv), index=False, encoding="utf-8")

def process_corpus(corpus_name, corpus, output_csv="./master_corpus.csv"):
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

def create_master_excel(corpora_dict, output_file="./master_corpus.xlsx"):
    """
    Creates a single Excel file consolidating all corpus data.
    
    :param corpora_dict: Dictionary where keys are corpus names and values are Corpus objects.
    :param output_file: Path to the master Excel file.
    """
    print(f"Creating master Excel file: {output_file}...")

    master_data = []  # List to collect all data before converting to DataFrame

    for corpus_name, corpus in corpora_dict.items():
        print(f"Processing corpus: {corpus_name}")

        for conversation in corpus.iter_conversations():
            conv_id = conversation.id
            res_id_counter = 1

            for utterance in conversation.iter_utterances():
                sanitized_answer = sanitize_text(utterance.text)
                
                master_data.append({
                    "corpus_name": corpus_name,
                    "conv_id": conv_id,
                    "res_id": res_id_counter,
                    "question_text": "DUMMY DATA",  # Placeholder for now
                    "answer_text": sanitized_answer
                })

                res_id_counter += 1
        
        print(f"Processed {len(master_data)} total entries so far...")

    # Convert to DataFrame
    df = pd.DataFrame(master_data)

    try:
        print(f"Writing master data to Excel file: {output_file}")
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"Master Excel file created successfully: {output_file}")
    except IllegalCharacterError as e:
        print(f"Error writing master Excel file: {e}")

# Run the Excel creation process
if __name__ == "__main__":
    CORPUS_DIR = "C:\\Users\\Connor Nesbit\\.convokit\\saved-corpora"
    start_time = time.time()
    TIME_LIMIT = 4 * 60 * 60  # 4 hours in seconds
    # MAX_CORPORA = 20
    # SKIP_ITEMS = 100
    # loaded_corpora = 0

    for index, item in enumerate(os.listdir(CORPUS_DIR)):
        if time.time() - start_time > TIME_LIMIT:
            print("Time limit reached (4 hours). Stopping corpus loading.")
            break

        if item == "downloads":
            continue

        # if index < SKIP_ITEMS:
        #     continue

        full_path = os.path.join(CORPUS_DIR, item)

        if os.path.isdir(full_path):  
            try:
                corpus = Corpus(filename=full_path)
                process_corpus(item, corpus)
                print(f"Loaded corpus from directory: {item}")
                # loaded_corpora += 1
                # if loaded_corpora >= MAX_CORPORA:
                #     break
            except Exception as e:
                print(f"Error loading corpus from directory {item}: {e}")
                break

    try:
        print("Converting CSV to Excel...")
        df = pd.read_csv("./master_corpus.csv", encoding="utf-8")
        df.to_excel("./master_corpus.xlsx", index=False, engine='openpyxl')
        print("Master Excel file created successfully.")
    except IllegalCharacterError as e:
        print(f"Error writing master Excel file: {e}")