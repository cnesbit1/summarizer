import os
import time
import subprocess
import pandas as pd
from rouge_score import rouge_scorer

# Paths
original_csv = "corpus_algorithms_and_models/corpus_data_downloads/data/reddit_corpus_small.csv"
gpt_scores_csv = "corpus_algorithms_and_models/corpus_summaries/rouge_scores_ollama_vs_original.csv"
summary_output_dir = "corpus_algorithms_and_models/corpus_summaries/ollama_conversation_summaries"
os.makedirs(summary_output_dir, exist_ok=True)

# Load data
df = pd.read_csv(original_csv)
df = df[df["text"].notnull()]
conversation_ids = df["conversation_id"].dropna().unique().tolist()

# ROUGE scorer
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
ollama_scores = []

# Summarization function using Ollama
def summarize_with_ollama(text, convo_id, model="llama3"):
    system_prompt = (
        "You are an extractive summarizer. "
        "Only select and return sentences copied verbatim from the original text. "
        "Do not rephrase or add words. "
        "Return the selected sentences in order, separated by newlines."
    )

    user_prompt = (
        "Extract a summary of about 10% of the text or up to 250 words "
        "by selecting only sentences from the original text exactly as written."
    )

    full_prompt = f"{system_prompt}\n\n{user_prompt}\n\n{text}"

    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=full_prompt.encode("utf-8"),
            capture_output=True,
            timeout=60  # prevent long stalls
        )
        output = result.stdout.decode("utf-8").strip()
        return output
    except Exception as e:
        print(f"Error with convo {convo_id}: {e}")
        return None

# Loop through conversations
for convo_id in conversation_ids:
    convo_df = df[df["conversation_id"] == convo_id]
    if convo_df.empty:
        continue

    original_text = "\n".join(str(t).strip() for t in convo_df["text"] if isinstance(t, str))
    summary_path = os.path.join(summary_output_dir, f"ollama_{convo_id}.txt")

    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            ollama_summary = f.read().strip()
    else:
        ollama_summary = summarize_with_ollama(original_text, convo_id)
        if ollama_summary:
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(ollama_summary)
        else:
            continue

    # Score
    scores = scorer.score(original_text, ollama_summary)
    ollama_scores.append({
        "conversation_id": convo_id,
        "rouge1_precision": scores["rouge1"].precision,
        "rouge1_recall": scores["rouge1"].recall,
        "rouge1_f1": scores["rouge1"].fmeasure,
        "rouge2_precision": scores["rouge2"].precision,
        "rouge2_recall": scores["rouge2"].recall,
        "rouge2_f1": scores["rouge2"].fmeasure,
        "rougeL_precision": scores["rougeL"].precision,
        "rougeL_recall": scores["rougeL"].recall,
        "rougeL_f1": scores["rougeL"].fmeasure
    })

    print(f"✓ {convo_id} — ROUGE-1 F1: {scores['rouge1'].fmeasure:.3f}")
    time.sleep(1.0)

# Save results
pd.DataFrame(ollama_scores).to_csv(gpt_scores_csv, index=False)
print(f"\nDone! Ollama ROUGE scores saved to: {gpt_scores_csv}")
