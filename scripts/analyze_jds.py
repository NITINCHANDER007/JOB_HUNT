import json
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

with open('apify_dataset_196.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

with open('resume_text.txt', 'r', encoding='utf-8') as f:
    resume_text = f.read().lower()

# Extract all descriptions from matched jobs
target_roles = ['data engineer', 'data scientist', 'data analyst', 'genai', 'generative ai', 'ai/ml', 'machine learning', 'ai engineer', 'ml engineer']

matched_descriptions = []
for j in jobs:
    t = (j.get('title') or '').lower()
    if any(r in t for r in target_roles):
        d = j.get('description') or ''
        if d:
            matched_descriptions.append(d)

print(f"Total matched JDs with descriptions: {len(matched_descriptions)}")

full_jd_corpus = " ".join(matched_descriptions).lower()

# Check common technical skills across Data Engineering, Data Science, GenAI, and AI/ML
tech_keywords = [
    # Data Engineering & Cloud
    'sql', 'python', 'spark', 'pyspark', 'hadoop', 'kafka', 'airflow', 'dbt', 'snowflake', 'databricks',
    'bigquery', 'redshift', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'etl', 'elt', 'data pipelines',
    'data warehousing', 'data lake', 'glue', 's3',
    # Data Science & ML
    'pandas', 'numpy', 'scikit-learn', 'xgboost', 'lightgbm', 'tensorflow', 'pytorch', 'keras',
    'statistics', 'hypothesis testing', 'eda', 'feature engineering', 'model evaluation', 'regression', 'classification',
    'mlflow', 'kubeflow', 'mlops', 'tableau', 'power bi',
    # GenAI & LLM
    'rag', 'langchain', 'langgraph', 'llamaindex', 'vector database', 'chromadb', 'faiss', 'pinecone', 'weaviate',
    'llm', 'llms', 'prompt engineering', 'fine-tuning', 'lora', 'qlora', 'hugging face', 'transformers',
    'openai', 'gemini', 'bedrock', 'claude', 'agents', 'agentic', 'embeddings', 'semantic search',
    # Software & Architecture
    'fastapi', 'flask', 'django', 'rest api', 'graphql', 'git', 'ci/cd', 'dsa', 'system design', 'oop'
]

keyword_counts = Counter()
for kw in tech_keywords:
    pattern = r'\b' + re.escape(kw) + r'\b'
    keyword_counts[kw] = len(re.findall(pattern, full_jd_corpus))

print("\n--- Top Skills in JDs vs Present in Resume ---")
for kw, count in keyword_counts.most_common(40):
    in_resume = kw in resume_text
    status = "✅ IN RESUME" if in_resume else "❌ MISSING IN RESUME"
    print(f"{kw:20s}: {count:4d} mentions | {status}")
