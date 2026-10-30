import json
from collections import Counter
from datetime import datetime

files = [
    'data/jobs_data.json',
    'data/scraped_jobs_raw.json',
    'data/filtered_data_jobs.json',
    'data/apify_dataset_196.json'
]

for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            d = json.load(f)
        print(f"=== {fpath} (count: {len(d)}) ===")
        sample = d[0] if d else {}
        print("  Keys:", list(sample.keys())[:8])
    except Exception as e:
        print(f"Error {fpath}: {e}")

