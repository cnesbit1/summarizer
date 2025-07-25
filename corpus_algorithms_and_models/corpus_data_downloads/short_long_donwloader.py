import os
import re
import logging
import pandas as pd
from convokit import Corpus, download

# Setup
logging.basicConfig(filename="corpus_download.log", level=logging.INFO, format="%(asctime)s - %(message)s")

SHORT_PATH = "short_conversations.csv"
LONG_PATH = "long_conversations.csv"
SHORT_LIMIT = 100
LONG_LIMIT = 100

short_convs = {}
long_convs = {}

def sanitize_text(text):
    return ''.join(c for c in (text or "") if c.isprintable())

def get_word_count(conversation):
    return sum(len((utt.text or "").split()) for utt in conversation.iter_utterances())

def save_conversations(conv_dict, path):
    all_rows = []
    for conv_id, conv_data in conv_dict.items():
        for res_id, utt in enumerate(conv_data["utterances"], start=1):
            all_rows.append({
                "corpus_name": conv_data["corpus_name"],
                "conv_id": conv_id,
                "res_id": res_id,
                "text": sanitize_text(utt.text)
            })
    pd.DataFrame(all_rows).to_csv(path, index=False)

def process_corpus(corpus_name):
    global short_convs, long_convs
    logging.info(f"Processing corpus: {corpus_name}")
    try:
        corpus_path = download(corpus_name)
        corpus = Corpus(filename=corpus_path)

        for conversation in corpus.iter_conversations():
            conv_id = conversation.id
            total_words = get_word_count(conversation)
            utts = list(conversation.iter_utterances())

            if SHORT_LIMIT > len(short_convs) and 100 <= total_words <= 200:
                short_convs[conv_id] = {
                    "corpus_name": corpus_name,
                    "utterances": utts
                }

            elif LONG_LIMIT > len(long_convs) and 1000 <= total_words <= 1500:
                long_convs[conv_id] = {
                    "corpus_name": corpus_name,
                    "utterances": utts
                }

            if len(short_convs) >= SHORT_LIMIT and len(long_convs) >= LONG_LIMIT:
                logging.info("Collected 100 short and 100 long conversations. Stopping.")
                return True

    except Exception as e:
        logging.error(f"Error processing corpus {corpus_name}: {e}")

    return False  # Continue

def main():
    corpus_names = [
        "subreddit-askscience", "subreddit-changemyview", "subreddit-askreddit", 
        "subreddit-explainlikeimfive", "subreddit-worldnews", "subreddit-news"
    ]

    for name in corpus_names:
        completed = process_corpus(name)
        if completed:
            break

    # Save to CSV
    save_conversations(short_convs, SHORT_PATH)
    save_conversations(long_convs, LONG_PATH)
    logging.info("Saved both CSV files.")

if __name__ == "__main__":
    main()
