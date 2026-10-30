import json

with open('data/scraped_jobs_raw.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

indeed = [j for j in raw if j.get('source') == 'Indeed']
print(f"Indeed jobs count: {len(indeed)}")
for j in indeed:
    print(f"  {j.get('company')} | {j.get('title')} | {j.get('location')} | {j.get('link')[:60]}")

