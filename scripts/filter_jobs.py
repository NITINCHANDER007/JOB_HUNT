import json
import re

with open('apify_dataset_196.json', 'r', encoding='utf-8') as f:
    raw_jobs = json.load(f)

print(f"Total raw jobs: {len(raw_jobs)}")

# We want:
# 1. Role: data roles (e.g. data engineer, data scientist, data analyst, etc.), genai, aiml
# 2. Location: Bangalore + Noida
# 3. Filter: Keep only titles that directly match [role], drop unrelated noise (e.g. generic Software Engineer listings)

target_role_patterns = [
    r'\bdata\s+engineer',
    r'\bdata\s+scientist',
    r'\bdata\s+science',
    r'\bdata\s+analyst',
    r'\bdata\s+analytics',
    r'\bbig\s+data',
    r'\bgen\s*ai',
    r'\bgenerative\s+ai',
    r'\bai\s*/?\s*ml',
    r'\bml\s*/?\s*ai',
    r'\bmachine\s+learning',
    r'\bartificial\s+intelligence',
    r'\bai\s+engineer',
    r'\bml\s+engineer',
    r'\bnlp\s+engineer',
    r'\bllm\b',
    r'\bdeep\s+learning',
    r'\bcomputer\s+vision',
    r'\bai\s+intern',
    r'\bml\s+intern',
    r'\bdata\s+intern',
    r'\bai\s+agent',
    r'\bapplied\s+scientist'
]

combined_role_regex = re.compile('|'.join(target_role_patterns), re.IGNORECASE)

# Drop generic software engineering roles unless explicitly data / ai / ml
generic_exclude_regex = re.compile(
    r'^(software engineer|software developer|backend developer|frontend developer|full stack developer|java developer|c\+\+ developer|qa engineer|test engineer|devops engineer|product manager|scrum master|business analyst)$',
    re.IGNORECASE
)

target_location_patterns = [
    r'bangalore',
    r'bengaluru',
    r'noida',
    r'greater noida',
    r'delhi',
    r'gurgaon',
    r'ncr'
]
combined_loc_regex = re.compile('|'.join(target_location_patterns), re.IGNORECASE)

matched_jobs = []
seen_job_keys = set()

for j in raw_jobs:
    title = (j.get('title') or '').strip()
    company = (j.get('companyName') or '').strip()
    location = (j.get('location') or '').strip()
    posted_date = j.get('postedTime') or j.get('publishedAt') or ''
    # If publishedAt is an ISO string like 2026-10-25T..., format it nicely
    if 'T' in str(posted_date) and '-' in str(posted_date):
        posted_date = str(posted_date).split('T')[0]
    
    apply_link = j.get('applyUrl') or j.get('jobUrl') or ''

    # Check title match
    if not combined_role_regex.search(title):
        continue

    # Exclude purely generic non-data titles
    if generic_exclude_regex.match(title.strip()):
        continue

    # Location check
    # Check if location contains Bangalore or Noida
    is_bangalore = bool(re.search(r'bangalore|bengaluru', location, re.I))
    is_noida = bool(re.search(r'noida', location, re.I))

    # Also check scrapingInfo location as secondary fallback if location field is general like "India"
    scraping_loc = (j.get('scrapingInfo', {}).get('location') or '')
    if not (is_bangalore or is_noida):
        if re.search(r'bangalore|bengaluru', scraping_loc, re.I):
            is_bangalore = True
        elif re.search(r'noida', scraping_loc, re.I):
            is_noida = True

    if not (is_bangalore or is_noida):
        continue

    # Normalized location string
    norm_loc = "Bengaluru, Karnataka" if is_bangalore else "Noida, Uttar Pradesh"
    if location and ('bengaluru' in location.lower() or 'bangalore' in location.lower() or 'noida' in location.lower()):
        norm_loc = location

    # Deduplicate by company + title
    dedup_key = f"{company.lower()}_{title.lower()}"
    if dedup_key in seen_job_keys:
        continue
    seen_job_keys.add(dedup_key)

    matched_jobs.append({
        'Job Title': title,
        'Company': company,
        'Location': norm_loc,
        'Posted Date': posted_date,
        'Apply Link': apply_link,
        'description': j.get('description') or ''
    })

print(f"Total matched data & AI roles in Bangalore + Noida: {len(matched_jobs)}")
for i, m in enumerate(matched_jobs[:20]):
    print(f"{i+1:2d}. {m['Job Title']} | {m['Company']} | {m['Location']} | {m['Posted Date']}")
