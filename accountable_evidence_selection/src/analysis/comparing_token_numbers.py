import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import os

# --- 1. Configuration ---
CSV_FILE_PATH = "data/Hepatitis txt vs. xml Grobid.csv"
PLOT_FILE_NAME = "plots/Avg_Response_Length_Comparison.png"

# --- 2. Data Loading (Using the confirmed headers) ---
def load_data_from_csv(file_path):
    # NOTE: Since we are using the comparison logic, we will assume the PDF column 
    # contains the XML output (as you noted the label mismatch in your previous runs).
    
    if not os.path.exists(file_path):
        print(f"Error: CSV file not found at {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path, keep_default_na=False)
        return df
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

# --- 3. Metric Function ---
def count_words(text):
    """
    Counts words/tokens by splitting on whitespace. 
    (Punctuation attached to words is included in the token count.)
    """
    # Ensure it's a string, then split by whitespace
    return len(str(text).split())

# --- 4. Main Execution and Plotting ---

df = load_data_from_csv(CSV_FILE_PATH)

if df is not None:
    # --- Calculation ---
    # Assign names based on your experiment roles
    df['XML_Word_Count'] = df['xml_response'].apply(count_words)
    df['TXT_Word_Count'] = df['txt_response'].apply(count_words)

    # --- Aggregation for Plotting ---
    avg_xml_length = df['XML_Word_Count'].mean()
    avg_txt_length = df['TXT_Word_Count'].mean()

    # Create summary DataFrame for visualization
    summary_data = pd.DataFrame({
        'Input Format': ['XML Input (GROBID)', 'TXT Input (Grobid LangChain)'],
        'Average Word Count': [avg_xml_length, avg_txt_length]
    })
    
    # Calculate the difference for text annotation
    word_diff = avg_xml_length - avg_txt_length
    percent_diff = (word_diff / avg_txt_length) * 100 if avg_txt_length else 0

    print("\n--- Summary Statistics ---")
    print(f"Average Word Count (XML Input): {avg_xml_length:.0f}")
    print(f"Average Word Count (TXT Input): {avg_txt_length:.0f}")
    print(f"XML Input generated {word_diff:.0f} more words ({percent_diff:.1f}%) on average.")

    # --- Plotting (Seaborn/Matplotlib) ---
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 7))

    # Use modern, professional color palette
    colors = ['#2E86AB', '#A23B72']  # Blue for XML, Purple for TXT
    
    barplot = sns.barplot(
        x='Input Format', 
        y='Average Word Count', 
        data=summary_data, 
        hue='Input Format',
        palette=colors,
        legend=False,
        ax=ax,
        edgecolor='white',
        linewidth=2
    )
    
    # Styling improvements
    plt.title('Average Response Length Comparison (XML vs. TXT)', 
              fontsize=18, fontweight='bold', pad=20)
    plt.ylabel('Average Response Length (Words)', fontsize=14, fontweight='semibold')
    plt.xlabel('Input Format', fontsize=14, fontweight='semibold')
    
    # Add data labels on top of bars with better styling
    for index, row in summary_data.iterrows():
        value = row['Average Word Count']
        barplot.text(index, value + 8, 
                    f"{value:.0f} words", 
                    color='#2C3E50', 
                    ha="center", 
                    fontsize=13,
                    fontweight='bold')
    
    # Add percentage difference annotation
    mid_y = (avg_xml_length + avg_txt_length) / 2
    ax.annotate(f'+{percent_diff:.1f}%\nmore words', 
                xy=(0.5, mid_y),
                xytext=(0.5, mid_y),
                ha='center',
                fontsize=11,
                color='#E63946',
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', 
                         facecolor='#FFE5E5', 
                         edgecolor='#E63946',
                         linewidth=1.5))
    
    # Improve tick labels
    ax.tick_params(axis='both', labelsize=12)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha='center')
    
    # Set y-axis to start from 0 for better visual comparison
    ax.set_ylim(0, max(avg_xml_length, avg_txt_length) * 1.15)
    
    # Remove top and right spines for cleaner look
    sns.despine(left=False, bottom=False)
    
    plt.tight_layout()
    plt.savefig(PLOT_FILE_NAME, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n✅ Bar Plot generated and saved as: {PLOT_FILE_NAME}")

    # --- Markdown Output for Presentation Script ---
    output_markdown = f"""
```markdown
### Visual Data: XML vs. TXT Output Detail (Word Count)

| Metric | XML Input (Structured) | TXT Input (LangChain) |
| :--- | :--- | :--- |
| **Average Response Length** | **{avg_xml_length:.0f} words** | {avg_txt_length:.0f} words |
| **Difference** | **{word_diff:.0f} words longer** | **{percent_diff:.1f}% more words** |

---
**Narrative Point:** Structured XML triggers a significant signal to the model, quantifying the retrieval of more detail and evidence.
```
"""
    
    print(output_markdown)