import pandas as pd

def clean_csv(input_file, output_csv, output_excel):
    df = pd.read_csv(input_file)
    df_cleaned = df.dropna(subset=['answer_text']).query("answer_text.str.strip() != ''")
    df_cleaned.to_csv(output_csv, index=False)
    df_cleaned.to_excel(output_excel, index=False)

input_file = "./master_corpus.csv"
output_csv = "./cleaned_master_corpus.csv"
output_excel = "master_corpus.xlsx"
clean_csv(input_file, output_csv, output_excel)
