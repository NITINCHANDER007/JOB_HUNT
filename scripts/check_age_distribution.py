import json
from datetime import datetime, date

with open('data/apify_dataset_196.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Total items in apify_dataset_196: {len(items)}")

today = date(2026, 10, 30)

age_buckets = {
    "Last 24 hours": 0,
    "2-7 days ago": 0,
    "8-14 days ago": 0,
    "15-30 days ago": 0,
    "> 30 days (Too old)": 0
}

valid_recent_jobs = []
too_old_jobs = []

for item in items:
    pa = item.get('publishedAt')
    pt = item.get('postedTime', '')
    if pa:
        try:
            d = datetime.strptime(pa, "%Y-%m-%d").date()
            diff_days = (today - d).days
            if diff_days <= 1:
                age_buckets["Last 24 hours"] += 1
            elif diff_days <= 7:
                age_buckets["2-7 days ago"] += 1
            elif diff_days <= 14:
                age_buckets["8-14 days ago"] += 1
            elif diff_days <= 30:
                age_buckets["15-30 days ago"] += 1
            else:
                age_buckets["> 30 days (Too old)"] += 1

            if diff_days <= 30:
                valid_recent_jobs.append((diff_days, pa, pt, item))
            else:
                too_old_jobs.append((diff_days, pa, pt, item))
        except Exception as e:
            pass

print("Age breakdown relative to today:")
for k, v in age_buckets.items():
    print(f"  {k}: {v} jobs")

print(f"\nTotal active jobs within <= 30 days: {len(valid_recent_jobs)}")
print(f"Total jobs older than 30 days: {len(too_old_jobs)}")

