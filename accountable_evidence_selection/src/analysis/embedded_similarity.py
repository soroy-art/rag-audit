import pandas as pd
import numpy as np
import re
import ollama
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import os

def _simple_tokenize(text: str):
    return re.findall(r"[A-Za-z0-9]+", text.lower())

def _ollama_embed_text(text: str, model: str):
    # Ensure you have 'ollama' installed: pip install ollama
    res = ollama.embed(model=model, input=text)
    return np.array(res.embeddings, dtype=np.float32)

def _token_embeddings(tokens, model: str, cache: dict):
    embs = []
    for tok in tokens:
        if tok in cache:
            emb = cache[tok]
        else:
            emb = _ollama_embed_text(tok, model)
            cache[tok] = emb
        embs.append(emb)
    return np.vstack(embs) if embs else np.empty((0, 0), dtype=np.float32)

def _cosine_matrix(A: np.ndarray, B: np.ndarray):
    A_norm = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9)
    B_norm = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-9)
    return np.dot(A_norm, B_norm.T)

def approx_bertscore_ollama(candidate_text: str, reference_text: str, ollama_model: str = "qwen3-embedding:latest"):
    cand_tokens = _simple_tokenize(candidate_text)
    ref_tokens = _simple_tokenize(reference_text)

    if not cand_tokens or not ref_tokens:
        return 0.0, 0.0, 0.0

    cache = {}
    try:
        A = _token_embeddings(cand_tokens, ollama_model, cache)
        B = _token_embeddings(ref_tokens, ollama_model, cache)
    except Exception as e:
        print(f"Ollama Error: {e}. Is Ollama running?")
        return 0.0, 0.0, 0.0

    M = _cosine_matrix(A, B)
    precision = float(M.max(axis=1).mean())
    recall = float(M.max(axis=0).mean())
    f1 = 0.0 if (precision + recall) == 0 else float(2 * precision * recall / (precision + recall))
    return precision, recall, f1

# --- 2. Standard Metrics (BLEU/ROUGE) ---
def calculate_bleu(ref, cand):
    ref_tokens = str(ref).lower().split()
    cand_tokens = str(cand).lower().split()
    if not ref_tokens or not cand_tokens: return 0.0
    return sentence_bleu([ref_tokens], cand_tokens, smoothing_function=SmoothingFunction().method1)

def calculate_rouge(ref, cand):
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    return scorer.score(str(ref), str(cand))['rougeL'].fmeasure

# --- 3. Main Comparison Logic ---
CSV_FILE = "evaluation_data.csv" # Ensure this has columns: txt_response, pdf_response, rag_response

def run_evaluation():
    if not os.path.exists(CSV_FILE):
        print("CSV not found.")
        return

    df = pd.read_csv(CSV_FILE, keep_default_na=False)
    results = []

    print(f"{'ID':<5} | {'Comp':<10} | {'BLEU':<6} | {'ROUGE':<6} | {'Embed-F1':<8}")
    print("-" * 50)

    for index, row in df.iterrows():
        qid = row.get('question_id', index)
        txt = row.get('txt_response', '')
        pdf = row.get('pdf_response', '')
        rag = row.get('rag_response', '') 

        # Comparison 1: TXT vs RAG
        b_tr = calculate_bleu(rag, txt)
        r_tr = calculate_rouge(rag, txt)
        _, _, f1_tr = approx_bertscore_ollama(txt, rag) # Semantic Score

        # Comparison 2: PDF vs RAG
        b_pr = calculate_bleu(rag, pdf)
        r_pr = calculate_rouge(rag, pdf)
        _, _, f1_pr = approx_bertscore_ollama(pdf, rag) # Semantic Score

        # Comparison 3: PDF vs TXT vs PDF
        b_tp = calculate_bleu(txt, pdf)
        r_tp = calculate_rouge(txt, pdf)
        _, _, f1_tp = approx_bertscore_ollama(txt, pdf) # Semantic Score

        results.append({
            "Question_ID": qid,
            "TXT_vs_RAG_BLEU": b_tr, "TXT_vs_RAG_ROUGE": r_tr, "TXT_vs_RAG_Semantic": f1_tr,
            "PDF_vs_RAG_BLEU": b_pr, "PDF_vs_RAG_ROUGE": r_pr, "PDF_vs_RAG_Semantic": f1_pr,
            "TXT_vs_PDF_BLEU": b_tp, "TXT_vs_PDF_ROUGE": r_tp, "TXT_vs_PDF_Semantic": f1_tp
        })

        print(f"{qid:<5} | TXT-RAG    | {b_tr:.3f}  | {r_tr:.3f}  | {f1_tr:.3f}")
        print(f"{qid:<5} | PDF-RAG    | {b_pr:.3f}  | {r_pr:.3f}  | {f1_pr:.3f}")
        print(f"{qid:<5} | TXT-PDF    | {b_tp:.3f}  | {r_tp:.3f}  | {f1_tp:.3f}")

    # Save
    pd.DataFrame(results).to_csv("final_comparison_results.csv", index=False)
    print("\nDone! Results saved.")

if __name__ == "__main__":
    run_evaluation()