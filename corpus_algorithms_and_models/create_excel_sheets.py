from openpyxl.utils.exceptions import IllegalCharacterError

import pickle
import os
import pandas as pd

def sanitize_text(text):
    if text is None:
        return ""
    # Remove non-printable characters and illegal characters
    return ''.join(char for char in text if char.isprintable() and ord(char) not in range(0x00, 0x20))

def create_excel_files(corpus_collection, corpus_names, output_dir="./input_data"):
    print(f"Creating output directory at {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    print("Output directory is ready.")

    for i, corpus in enumerate(corpus_collection):
        print(f"Processing corpus: {corpus_names[i]}")
        
        data = {
            "conv_id": [],
            "res_id": [],
            "question_text": [],
            "answer_text": [],
        }

        excel_path = os.path.join(output_dir, f"{corpus_names[i]}.xlsx")
        if os.path.exists(excel_path):
            print(f"File '{excel_path}' already exists. Skipping...")
            continue

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
        
        print(f"Processed {len(data['conv_id'])} responses for '{corpus_names[i]}'.")
        
        df = pd.DataFrame(data)
        
        try:
            print(f"Writing data to Excel file: {excel_path}")
            df.to_excel(excel_path, index=False, engine='openpyxl')
            print(f"Excel file created for '{corpus_names[i]}': {excel_path}")
        except IllegalCharacterError as e:
            print(f"Error writing to Excel for {corpus_names[i]}: {e}")

if __name__ == "__main__":
    with open("corpora_data.pkl", "rb") as file:
        corpus_collection, all_corpus_names = pickle.load(file)
        print("Loaded corpus data from 'corpora_data.pkl'.")

    print("Starting Excel file creation process...")
    create_excel_files(corpus_collection, all_corpus_names)
    print("Excel file creation process completed.")