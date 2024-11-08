from convokit import TextCleaner, Corpus, download
import pandas as pd
import os

def download_corpora(main_corpus_name, subreddit_names):

    main_corpus = Corpus(filename=download(main_corpus_name))
    corpus_collection = [main_corpus]
    text_cleaner = TextCleaner()
    
    for name in subreddit_names:
        corpus = Corpus(filename=download(name))
        text_cleaner.transform(corpus)
        corpus_collection.append(corpus)
    
    all_corpus_names = subreddit_names + [main_corpus_name]
    
    print(f"Downloaded {len(corpus_collection)} corpora.")
    
    return corpus_collection, all_corpus_names

def create_excel_files(corpus_collection, corpus_names, output_dir="./input_data"):
    os.makedirs(output_dir, exist_ok=True)
    
    for i, corpus in enumerate(corpus_collection):
        data = {
            "Conversation ID": [],
            "Utterance ID": [],
            "Speaker ID": [],
            "Reply to": [],
            "Text": [],
            "Timestamp": []
        }

        for conversation in corpus.iter_conversations():
            for utterance in conversation.iter_utterances():
                data["Conversation ID"].append(conversation.id)
                data["Utterance ID"].append(utterance.id)
                data["Speaker ID"].append(utterance.speaker.id)
                data["Reply to"].append(utterance.reply_to or "N/A")
                data["Text"].append(utterance.text)
                data["Timestamp"].append(utterance.timestamp)

        df = pd.DataFrame(data)
        excel_path = os.path.join(output_dir, f"{corpus_names[i]}.xlsx")
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"Excel file created for {corpus_names[i]}: {excel_path}")


main_corpus_name = "reddit-corpus-small"
subreddit_names = ["subreddit-Cornell", "subreddit-NATOsubreddit", "subreddit-NBAOdds", "subreddit-NBC_TV"]
corpus_collection, all_corpus_names = download_corpora(main_corpus_name, subreddit_names)

if __name__ == "__main__":
    create_excel_files(corpus_collection, all_corpus_names)
