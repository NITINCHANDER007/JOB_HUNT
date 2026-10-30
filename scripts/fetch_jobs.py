import urllib.request
import json
import os

token = os.getenv("APIFY_TOKEN", "")

# 1. Fetch Indeed dataset
indeed_items = []
try:
    indeed_url = f'https://api.apify.com/v2/datasets/fH4a0ofbJKF3BaTYz/items?token={token}&format=json'
    with urllib.request.urlopen(indeed_url) as resp:
        indeed_items = json.loads(resp.read().decode('utf-8'))
except Exception as e:
    print('Error fetching Indeed dataset:', e)

# 2. Fetch LinkedIn dataset
li_items = []
try:
    li_url = f'https://api.apify.com/v2/datasets/fXF4O0Md1A55ab0mL/items?token={token}&format=json'
    with urllib.request.urlopen(li_url) as resp:
        li_items = json.loads(resp.read().decode('utf-8'))
except Exception as e:
    print('Error fetching LinkedIn dataset:', e)

print(f'Indeed: {len(indeed_items)}, LinkedIn: {len(li_items)}')

all_jobs = []
for item in indeed_items:
    salary_val = item.get('salary')
    if not salary_val:
        salary_val = "₹15,000 - ₹35,000 / month (Est. Internship stipend)"
    all_jobs.append({
        'source': 'Indeed',
        'title': item.get('positionName'),
        'company': item.get('company'),
        'location': item.get('location'),
        'salary': salary_val,
        'link': item.get('externalApplyLink') or item.get('url'),
        'description': (item.get('description') or '')[:500]
    })

for item in li_items:
    s_min = item.get('salaryMin')
    s_max = item.get('salaryMax')
    s_curr = item.get('salaryCurrency') or 'INR'
    s_period = item.get('salaryPeriod') or 'month'
    if s_min or s_max:
        salary_str = f"{s_curr} {s_min or ''} - {s_max or ''} / {s_period}".strip()
    else:
        salary_str = "₹20,000 - ₹45,000 / month (Est. Market rate)"

    all_jobs.append({
        'source': 'LinkedIn',
        'title': item.get('title'),
        'company': item.get('companyName'),
        'location': item.get('location'),
        'salary': salary_str,
        'link': item.get('applyUrl') or item.get('jobUrl'),
        'description': (item.get('description') or '')[:500]
    })

with open('scraped_jobs_raw.json', 'w', encoding='utf-8') as f:
    json.dump(all_jobs, f, indent=2)

print('Saved', len(all_jobs), 'raw jobs to scraped_jobs_raw.json')
