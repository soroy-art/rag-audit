import pandas as pd
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import os

# --- 1. Configuration ---
# Ensure your CSV file has headers: 'question_id', 'txt_response', 'pdf_response'
CSV_FILE_PATH = "evaluation_data.csv" 

# --- 2. Data Loading ---
def load_data_from_csv(file_path):
    if not os.path.exists(file_path):
        print(f"Error: CSV file not found at {file_path}")
        return []
    try:
        df = pd.read_csv(file_path, keep_default_na=False)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

# --- 3. Metric Calculation Functions ---
def calculate_bleu(text1, text2):
    """Calculates BLEU score (0 to 1) between two texts."""
    # Tokenize by splitting on whitespace
    tokens1 = str(text1).lower().split()
    tokens2 = str(text2).lower().split()
    
    if not tokens1 or not tokens2:
        return 0.0

    # Smoothing is critical for short sentences
    smoothie = SmoothingFunction().method1
    # We treat text1 as the 'reference' and text2 as the 'candidate'
    # For similarity, the order matters less, but consistency is key.
    return sentence_bleu([tokens1], tokens2, smoothing_function=smoothie)

def calculate_rouge(text1, text2):
    """Calculates ROUGE-L F1 score (0 to 1) between two texts."""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(str(text1), str(text2))
    return scores['rougeL'].fmeasure

# --- 4. Main Execution ---

data = load_data_from_csv(CSV_FILE_PATH)

if data:
    results = []
    print(f"{'ID':<5} | {'BLEU (Sim)':<10} | {'ROUGE-L (Sim)':<12} | {'Interpretation'}")
    print("-" * 60)

    for item in data:
        # Calculate similarity between the two model outputs
        bleu_sim = calculate_bleu(item['txt_response'], item['pdf_response'])
        rouge_sim = calculate_rouge(item['txt_response'], item['pdf_response'])
        
        # Combined interpretation using both scores
        if bleu_sim > 0.5 and rouge_sim > 0.6:
            interpretation = "High Agreement (consistent wording & content)"
        elif bleu_sim < 0.3 and rouge_sim > 0.5:
            interpretation = "Semantic Agreement (same ideas, different wording)"
        elif bleu_sim > 0.4 and rouge_sim < 0.5:
            interpretation = "Surface Similarity (similar phrases, different meaning)"
        elif rouge_sim > 0.4:
            interpretation = "Moderate Divergence"
        else:
            interpretation = "CRITICAL DISAGREEMENT"
        
        results.append({
            "Question_ID": item.get('question_id', 'N/A'),
            "Guideline": item.get('guideline', 'N/A'),
            "BLEU_Similarity": bleu_sim,
            "ROUGE_Similarity": rouge_sim,
            "Interpretation": interpretation
        })

        print(f"{item.get('question_id', 'N/A'):<5} | {bleu_sim:.3f}     | {rouge_sim:.3f}       | {interpretation}")

    # --- 5. Save & Summarize ---
    results_df = pd.DataFrame(results)
    results_df['BLEU_Similarity'] = results_df['BLEU_Similarity'].round(3)
    results_df['ROUGE_Similarity'] = results_df['ROUGE_Similarity'].round(3)
    
    print("\n--- Summary of Consistency ---")
    print(f"Average BLEU Similarity:  {results_df['BLEU_Similarity'].mean():.3f}")
    print(f"Average ROUGE Similarity: {results_df['ROUGE_Similarity'].mean():.3f}")
    
    output_filename = "model_comparison_results.csv"
    results_df.to_csv(output_filename, index=False)
    print(f"\nDetailed comparison saved to '{output_filename}'")