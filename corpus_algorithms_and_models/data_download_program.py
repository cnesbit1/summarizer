from convokit import TextCleaner, Corpus, download
import pandas as pd
import os

from openpyxl.utils.exceptions import IllegalCharacterError

def sanitize_text(text):
    if text is None:
        return ""
    # Remove non-printable characters and illegal characters
    return ''.join(char for char in text if char.isprintable() and ord(char) not in range(0x00, 0x20))

def download_corpora(main_corpus_name, subreddit_names):
    print(f"Downloading main corpus: {main_corpus_name}")
    main_corpus = Corpus(filename=download(main_corpus_name))
    print(f"Main corpus '{main_corpus_name}' downloaded with {len(main_corpus.get_conversation_ids())} conversations.")
    
    corpus_collection = [main_corpus]
    # text_cleaner = TextCleaner()
    
    for name in subreddit_names:
        print(f"Downloading subreddit corpus: {name}")
        corpus = Corpus(filename=download(name))
        print(f"Subreddit corpus '{name}' downloaded with {len(corpus.get_conversation_ids())} conversations.")
        
        # print(f"Applying text cleaning to '{name}'...")
        # text_cleaner.transform(corpus)
        # print(f"Text cleaning completed for '{name}'.")
        
        corpus_collection.append(corpus)
    
    all_corpus_names = subreddit_names + [main_corpus_name]
    print(f"Downloaded {len(corpus_collection)} corpora in total.")
    
    return corpus_collection, all_corpus_names

def create_excel_files(corpus_collection, corpus_names, output_dir="./input_data"):
    print(f"Creating output directory at {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    print("Output directory is ready.")
    
    def sanitize_text(text):
        if text is None:
            return ""
        return ''.join(char for char in text if char.isprintable() and ord(char) not in range(0x00, 0x20))

    for i, corpus in enumerate(corpus_collection):
        print(f"Processing corpus: {corpus_names[i]}")
        
        data = {
            "conv_id": [],
            "res_id": [],
            "question_text": [],
            "answer_text": [],
        }

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
        excel_path = os.path.join(output_dir, f"{corpus_names[i]}.xlsx")
        
        try:
            print(f"Writing data to Excel file: {excel_path}")
            df.to_excel(excel_path, index=False, engine='openpyxl')
            print(f"Excel file created for '{corpus_names[i]}': {excel_path}")
        except IllegalCharacterError as e:
            print(f"Error writing to Excel for {corpus_names[i]}: {e}")


# Main program
main_corpus_name = "subreddit-corpus"
subreddit_names = ["subreddit-Cornell", "subreddit-NATOsubreddit", "subreddit-NBAOdds", "subreddit-NBC_TV"]

print("Starting the corpus downloading process...")
corpus_collection, all_corpus_names = download_corpora(main_corpus_name, subreddit_names)
print("Corpus downloading completed.")

if __name__ == "__main__":
    print("Starting Excel file creation process...")
    create_excel_files(corpus_collection, all_corpus_names)
    print("Excel file creation process completed.")
