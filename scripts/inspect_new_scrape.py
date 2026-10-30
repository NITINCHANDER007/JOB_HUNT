import json

def load_apify_output(path):
    with open(path, 'r', encoding='utf-8') as f:
        line = f.readline()
    data = json.loads(line)
    return data.get('items', [])

items1 = load_apify_output(r'C:\Users\Lenovo\.gemini\antigravity\brain\eeb355af-5833-4332-a19e-a81b4c3cb394\.system_generated\steps\1901\output.txt')
items2 = load_apify_output(r'C:\Users\Lenovo\.gemini\antigravity\brain\eeb355af-5833-4332-a19e-a81b4c3cb394\.system_generated\steps\1925\output.txt')
all_items = items1 + items2
print('Total scraped items:', len(all_items))

unique_by_url = {}
for it in all_items:
    url = it.get('jobUrl') or it.get('id')
    if url and url not in unique_by_url:
        unique_by_url[url] = it
print('Unique scraped items:', len(unique_by_url))

with open('data/fresh_linkedin_scraped.json', 'w', encoding='utf-8') as f:
    json.dump(list(unique_by_url.values()), f, indent=2)
print('Saved to data/fresh_linkedin_scraped.json')

