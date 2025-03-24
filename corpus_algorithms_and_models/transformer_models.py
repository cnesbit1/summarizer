from convokit import Transformer

import os
from convokit import Corpus

CORPUS_DIR = "C:\\Users\\Connor Nesbit\\.convokit\\saved-corpora"
corpora = {}

for item in os.listdir(CORPUS_DIR):
    if item == "downloads":
        continue
    full_path = os.path.join(CORPUS_DIR, item)

    if os.path.isdir(full_path):  
        try:
            corpora[item] = Corpus(filename=full_path)
            print(f"Loaded corpus from directory: {item}")
        except Exception as e:
            print(f"Error loading corpus from directory {item}: {e}")

    else:
        continue



print("Starting Excel file creation process...")
create_excel_files(corpus_collection, all_corpus_names)
print("Excel file creation process completed.")

# Print summary of loaded corpora
for name, corpus in corpora.items():
    print(f"\nCorpus: {name}")
    print(corpus.summary())
