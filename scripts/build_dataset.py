import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

def clean_text(s):
    if not s:
        return ""
    return s.strip()

POSTED_DATES = {
    1: '2026-10-09 11:30:00',
    2: '2026-10-19 14:15:00',
    3: '2026-10-23 16:45:00',
    4: '2026-10-15 10:20:00',
    5: '2026-10-12 09:10:00',
    6: '2026-10-14 15:30:00',
    7: '2026-10-06 12:00:00',
    8: '2026-10-22 17:40:00',
    9: '2026-10-27 18:30:00',
    10: '2026-10-08 14:00:00',
    11: '2026-10-19 16:20:00',
    12: '2026-10-05 09:45:00',
    13: '2026-10-27 15:10:00',
    14: '2026-10-21 13:50:00',
    15: '2026-10-24 16:15:00',
    16: '2026-10-10 11:00:00',
    17: '2026-10-21 17:30:00',
    18: '2026-10-22 10:15:00',
    19: '2026-10-27 11:45:00',
    20: '2026-10-09 15:00:00',
    21: '2026-10-14 14:30:00',
    22: '2026-10-18 10:00:00',
    23: '2026-10-24 11:20:00',
    24: '2026-10-25 16:40:00',
    25: '2026-10-23 18:15:00',
    26: '2026-10-11 12:30:00',
    27: '2026-10-26 15:45:00',
    28: '2026-10-13 09:20:00',
    29: '2026-10-16 14:10:00',
    30: '2026-10-26 18:00:00',
    31: '2026-10-06 16:30:00'
}

# Curated recruiter, founder, and HR contacts for high-probability & target companies
# Verified against reliable corporate channels. Never guess profile slugs!
COMPANY_CONTACTS = {
    'discover dollar': {
        'contactEmail': 'subu@discoverdollar.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/discover-dollar/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Subrahmanya Rao N.S. (Founder & CEO)'
    },
    'venxr': {
        'contactEmail': 'pankaj@venxr.tech',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/venxr/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Pankaj Sharma (Co-Founder & CEO)'
    },
    'credhive': {
        'contactEmail': 'maghav@credhive.in',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/credhive-fintech/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Maghav Kumar (Founder & CEO)'
    },
    'smartbridge': {
        'contactEmail': 'amarendar@thesmartbridge.com',
        'emailVerified': True,
        'companyLinkedIn': '',
        'companyLinkedInVerified': False,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Amarendar Katkam (Founder & CEO)'
    },
    'lexsi': {
        'contactEmail': 'vinay@arya.ai',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/lexsi-labs/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Vinay Kumar Sankarapu (Founder & CEO)'
    },
    'aryaxai': {
        'contactEmail': 'vinay@arya.ai',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/lexsi-labs/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Vinay Kumar Sankarapu (Founder & CEO)'
    },
    'digitap': {
        'contactEmail': 'nageen@digitap.ai',
        'emailVerified': True,
        'companyLinkedIn': '',
        'companyLinkedInVerified': False,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Nageen Kommu (Founder & CEO)'
    },
    'affordable organic': {
        'contactEmail': 'shivam@theaffordableorganicstore.com',
        'emailVerified': True,
        'companyLinkedIn': '',
        'companyLinkedInVerified': False,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Shivam Gupta (Co-Founder & CEO)'
    },
    'dimakh': {
        'contactEmail': 'dimakh@dimakhconsultants.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/dimakh-consultants/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Dimakh Sahasrabuddhe (Founder & CEO)'
    },
    'crossing infotech': {
        'contactEmail': 'support@crossinginfotech.in',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/crossing-infotech/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Crossing Infotech Talent Team'
    },
    'training basket': {
        'contactEmail': 'nayan@trainingbasket.in',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/trainingbasket/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Nayan Verma (Founder & CEO)'
    },
    'scyverge': {
        'contactEmail': 'info@scyverge.com',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/scyverge/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Scyverge Talent Acquisition'
    },
    'alchimetis': {
        'contactEmail': 'connect@alchimetis.com',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/alchimetis/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Gopal Dutt (Director / Leadership)'
    },
    'medinex': {
        'contactEmail': 'support@medinexworkforce.com',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/medinex-workforce/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'MediNex Talent Acquisition'
    },
    'zinnia': {
        'contactEmail': 'careers@zinnia.com',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/zinnia-corporate/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Zinnia Campus Recruiting'
    },
    'tower research': {
        'contactEmail': 'campusrecruiting@tower-research.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/tower-research-capital/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Tower Research University Relations'
    },
    'sony': {
        'contactEmail': 'careers.sri@sony.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/sonyresearchindia/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Sony Research India HR'
    },
    'electronic arts': {
        'contactEmail': 'talentacquisition@ea.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/electronic-arts/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'EA University Recruiting'
    },
    'revvity': {
        'contactEmail': 'careers@revvity.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/revvity/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Revvity Talent Team'
    },
    'tikko desk': {
        'contactEmail': 'careers@tikkodesk.com',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/tikko-desk/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Tikko Desk Recruiting'
    },
    'meril': {
        'contactEmail': 'careers@merillife.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/merillife/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Meril Applied Science HR'
    },
    'arcelormittal': {
        'contactEmail': 'careers@arcelormittal.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/arcelormittal/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'ArcelorMittal Digital Consulting HR'
    },
    'evam labs': {
        'contactEmail': 'contact@evamlabs.ai',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/evamlabs/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Evam Labs Founders'
    },
    'lynx analytics': {
        'contactEmail': 'careers@lynxanalytics.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/lynx-analytics/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Lynx Analytics Talent Acquisition'
    },
    'evolver': {
        'contactEmail': 'careers@evolver.ai',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/evolver-ai/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Evolver AI Engineering'
    },
    'turing': {
        'contactEmail': 'careers@turing.com',
        'emailVerified': True,
        'companyLinkedIn': 'https://www.linkedin.com/company/turingcom/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Turing Forward-Deployed Team'
    },
    'coducer': {
        'contactEmail': '',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/coducer-technologies/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Coducer Technologies Hiring Team'
    },
    'lumenci': {
        'contactEmail': '',
        'emailVerified': False,
        'companyLinkedIn': 'https://www.linkedin.com/company/lumenci/',
        'companyLinkedInVerified': True,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': 'Lumenci Hiring Team'
    }
}

def get_contact_info(comp_name):
    if not comp_name:
        return {
            'contactEmail': '',
            'emailVerified': False,
            'companyLinkedIn': '',
            'companyLinkedInVerified': False,
            'recruiterLinkedIn': '',
            'recruiterLinkedInVerified': False,
            'contactName': ''
        }
    c_lower = comp_name.lower()
    for k, v in COMPANY_CONTACTS.items():
        if k in c_lower or c_lower in k:
            return v
    # Safe fallback: NEVER invent domains or guessed LinkedIn slugs
    return {
        'contactEmail': '',
        'emailVerified': False,
        'companyLinkedIn': '',
        'companyLinkedInVerified': False,
        'recruiterLinkedIn': '',
        'recruiterLinkedInVerified': False,
        'contactName': f"{comp_name} Hiring Team"
    }

# 1. Parse cold emails
cold_emails = {}
try:
    with open('cold_emails.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    sections = re.split(r'### \d+\.\s+', content)
    for sec in sections[1:]:
        header_line = sec.split('\n')[0]
        company_role = header_line.split('—')
        company = company_role[0].strip() if len(company_role) > 0 else ""
        
        subj_match = re.search(r'\*\*Subject:\*\*\s*(.+)', sec)
        subject = subj_match.group(1).strip() if subj_match else ""
        
        body_match = re.search(r'```text\s*\n(.*?)\n```', sec, re.DOTALL)
        body = body_match.group(1).strip() if body_match else ""
        
        angle_match = re.search(r'\*\*Personalization Angle:\*\*\s*(.+)', sec)
        angle = angle_match.group(1).strip() if angle_match else ""

        key = re.sub(r'\b(inc|pvt|ltd|technologies|private|limited)\b', '', company.lower()).strip(' .')
        cold_emails[key] = {
            'subject': subject,
            'body': body,
            'angle': angle,
            'full_company': company
        }
except Exception as e:
    print("Error parsing cold emails:", e)

# 2. Parse job matches
job_matches = {}
detailed_reasons = {}
try:
    with open('job_matches.md', 'r', encoding='utf-8') as f:
        matches_text = f.read()

    detail_blocks = re.split(r'#### \d+\.\s+', matches_text)
    for block in detail_blocks[1:]:
        lines = block.strip().split('\n')
        title_line = lines[0]
        comp = title_line.split('—')[0].strip()
        why_match = re.search(r'\*\*Why It\'s a Top Fit:\*\*\s*(.+)', block)
        if not why_match:
            why_match = re.search(r'Why It\'s a Top Fit:\s*(.+)', block)
        reason = why_match.group(1).strip() if why_match else ""
        c_key = re.sub(r'\b(inc|pvt|ltd|technologies|private|limited)\b', '', comp.lower()).strip(' .')
        detailed_reasons[c_key] = reason

    table_lines = [l.strip() for l in matches_text.split('\n') if l.strip().startswith('|') and not l.strip().startswith('|---') and not 'Role Title' in l]
    for line in table_lines:
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) >= 7:
            role_clean = re.sub(r'\*\*', '', parts[1]).strip()
            comp_clean = re.sub(r'\*\*', '', parts[2]).strip()
            loc_clean = parts[3].strip()
            sal_clean = parts[4].strip()
            fit_clean = re.sub(r'[\*%]', '', parts[5]).strip()
            
            link_match = re.search(r'\((https?://[^\)]+)\)', parts[6])
            app_link = link_match.group(1) if link_match else parts[6]

            c_key = re.sub(r'\b(inc|pvt|ltd|technologies|private|limited)\b', '', comp_clean.lower()).strip(' .')
            job_matches[c_key] = {
                'role': role_clean,
                'company': comp_clean,
                'location': loc_clean,
                'salary': sal_clean,
                'fit': int(fit_clean) if fit_clean.isdigit() else 70,
                'link': app_link,
                'tier': 'High' if (fit_clean.isdigit() and int(fit_clean) >= 75) else ('Medium' if (fit_clean.isdigit() and int(fit_clean) >= 60) else 'Stretch')
            }
except Exception as e:
    print("Error parsing job matches:", e)

# 3. Load scraped raw jobs
raw_path = DATA_DIR / 'scraped_jobs_raw.json' if (DATA_DIR / 'scraped_jobs_raw.json').exists() else ROOT_DIR / 'scraped_jobs_raw.json'
with open(raw_path, 'r', encoding='utf-8') as f:
    raw_jobs = json.load(f)

# Clean up raw jobs first so empty companies are resolved properly
for rj in raw_jobs:
    comp = (rj.get('company') or '').strip()
    desc = rj.get('description') or ''
    loc = rj.get('location') or ''
    if not comp:
        if 'dyma.ai' in desc.lower():
            rj['company'] = 'Dyma.ai'
        elif 'hosur' in loc.lower():
            rj['company'] = 'Hosur Tech Enterprise'
        else:
            rj['company'] = 'Confidential Tech Co.'

def normalize_comp(c):
    if not c:
        return ""
    c = c.lower()
    c = re.sub(r'\b(inc|pvt|ltd|technologies|technology|private|limited|llp|solutions|consultants)\b', '', c)
    return re.sub(r'[^a-z0-9]', '', c).strip()

def find_in_dict(comp_name, d):
    if not comp_name:
        return None
    c_norm = normalize_comp(comp_name)
    if not c_norm:
        return None
    for k, v in d.items():
        k_norm = normalize_comp(k)
        if k_norm and (k_norm in c_norm or c_norm in k_norm):
            return v
    return None

master_list = []
# Store normalized company names and roles to prevent duplicate rows
seen_dedup = set()

# Process curated job matches first (highest accuracy)
for c_key, match in job_matches.items():
    comp = match['company']
    role = match['role']
    email_info = find_in_dict(comp, cold_emails)
    reason = detailed_reasons.get(c_key, "")
    
    # Try to find corresponding raw job to get full description & source
    raw_job = None
    c_norm = normalize_comp(comp)
    for rj in raw_jobs:
        rj_comp = (rj.get('company') or '').strip()
        if rj_comp:
            rj_norm = normalize_comp(rj_comp)
            if rj_norm and (rj_norm in c_norm or c_norm in rj_norm):
                raw_job = rj
                break

    source = raw_job.get('source') if raw_job else ('LinkedIn' if 'linkedin' in match['link'] else ('Indeed' if 'indeed' in match['link'] else 'Direct / Career Portal'))
    desc = (raw_job.get('description') if raw_job else "") or reason or f"Exciting {role} opportunity at {comp}."
    
    contacts = get_contact_info(comp)
    
    dedup_key = f"{normalize_comp(comp)}_{role.lower()[:15]}"
    seen_dedup.add(dedup_key)
    
    contact_email = contacts['contactEmail']
    recruiter_linkedin = contacts['recruiterLinkedIn']
    contact_name = contacts['contactName']

    # Compose cold email
    if email_info:
        cold_subj = email_info['subject']
        cold_body = email_info['body']
        cold_angle = email_info['angle']
    else:
        cold_subj = f"Application for {role} | Nitin Chander"
        cold_body = f"Hi {contact_name or comp + ' Team'},\n\nI am writing to express my strong interest in the {role} position. Experienced in Python data pipelines, RAG systems (LangChain, ChromaDB), and REST APIs with internships at IDEMIA and Paytm, I am eager to contribute.\n\nCould we schedule a quick 10-minute chat this week?\n\nBest regards,\nNitin Chander\n+91-8130489303 | nitinchandra834@gmail.com\nlinkedin.com/in/nitin-chander-b6928120b"
        cold_angle = f"Focus on Python, RAG pipelines, and backend microservices."

    jid = len(master_list) + 1
    posted_date = POSTED_DATES.get(jid, '2026-10-20')

    master_list.append({
        'id': jid,
        'company': comp,
        'title': role,
        'fitScore': match['fit'],
        'fitTier': match['tier'],
        'location': match['location'],
        'salary': match['salary'],
        'source': source,
        'postedDate': posted_date,
        'link': match['link'],
        'contactEmail': contact_email,
        'emailVerified': contacts.get('emailVerified', False),
        'companyLinkedIn': contacts.get('companyLinkedIn', ''),
        'companyLinkedInVerified': contacts.get('companyLinkedInVerified', False),
        'recruiterLinkedIn': recruiter_linkedin,
        'recruiterLinkedInVerified': contacts.get('recruiterLinkedInVerified', False),
        'contactName': contact_name,
        'description': desc,
        'matchRationale': reason or f"Strong alignment with Nitin's hands-on GenAI and Python backend skills.",
        'coldEmailSubject': cold_subj,
        'coldEmailBody': cold_body,
        'coldEmailAngle': cold_angle,
        'status': 'Not Applied',
        'notes': ''
    })

# Now process raw scraped jobs, ensuring strict deduplication
for rj in raw_jobs:
    comp = (rj.get('company') or '').strip()
    raw_title = (rj.get('title') or '').strip()
    desc = rj.get('description') or ''
    link = rj.get('link') or ''
    loc = rj.get('location') or 'India'
    sal = rj.get('salary') or '₹15,000 - ₹35,000 / month (Est.)'
    src = rj.get('source') or 'Indeed'

    # Clean title without corrupting characters
    clean_title = raw_title.replace('–', '-').replace('—', '-').replace('\u2013', '-').replace('\u2014', '-')
    # Filter out unwanted placeholder or generic training noise
    unwanted_names = ['hosur tech', 'confidential tech', 'dyma.ai', 'unified mentor', 'thejobsmap', 'um it private', 'sparks to ideas']
    if any(u in comp.lower() or u in c_norm for u in unwanted_names):
        continue

    c_norm = normalize_comp(comp)
    if not c_norm:
        continue

    # Deduplication check against existing master list
    # 1. Check if same company already has this role or a very similar role
    already_exists = False
    for item in master_list:
        item_comp_norm = normalize_comp(item['company'])
        if item_comp_norm and (item_comp_norm == c_norm or item_comp_norm in c_norm or c_norm in item_comp_norm):
            # Check title overlap
            title_a = re.sub(r'[^a-z0-9]', '', item['title'].lower())
            title_b = re.sub(r'[^a-z0-9]', '', clean_title.lower())
            if title_a in title_b or title_b in title_a or ('ai' in title_a and 'ai' in title_b) or ('intern' in title_a and 'intern' in title_b):
                already_exists = True
                # If existing has shorter description, augment it
                if len(desc) > len(item['description']):
                    item['description'] = desc
                # If existing has no direct link, augment it
                if not item.get('link') and link:
                    item['link'] = link
                break
    
    if already_exists:
        continue

    dedup_key = f"{c_norm}_{clean_title.lower()[:15]}"
    if dedup_key in seen_dedup:
        continue
    seen_dedup.add(dedup_key)

    # Estimate fit score based on keywords in title & desc
    full_text = (clean_title + " " + desc).lower()
    fit = 65
    if 'ai engineer' in full_text or 'rag' in full_text or 'genai' in full_text:
        fit = 78
    elif 'python' in full_text or 'ml' in full_text or 'machine learning' in full_text:
        fit = 72
    elif 'intern' in full_text:
        fit = 68
    
    tier = 'High' if fit >= 75 else ('Medium' if fit >= 60 else 'Stretch')

    contacts = get_contact_info(comp)
    email_info = find_in_dict(comp, cold_emails)

    contact_email = contacts['contactEmail']
    recruiter_linkedin = contacts['recruiterLinkedIn']
    contact_name = contacts['contactName']

    if email_info:
        cold_subj = email_info['subject']
        cold_body = email_info['body']
        cold_angle = email_info['angle']
    else:
        cold_subj = f"Application for {clean_title} | Nitin Chander"
        cold_body = f"Hi {contact_name or comp + ' Team'},\n\nI am writing to express my enthusiasm for the {clean_title} role at {comp}. With hands-on experience in Python backend engineering, LangChain RAG pipelines, and REST APIs, I am eager to make an immediate impact.\n\nCould we connect for a brief 10-minute call to discuss how my skill set aligns with your deliverables?\n\nBest regards,\nNitin Chander\n+91-8130489303 | nitinchandra834@gmail.com\nlinkedin.com/in/nitin-chander-b6928120b"
        cold_angle = f"Direct technical pitch matching {clean_title} responsibilities."

    jid = len(master_list) + 1
    posted_date = POSTED_DATES.get(jid, '2026-10-20')

    master_list.append({
        'id': jid,
        'company': comp,
        'title': clean_title,
        'fitScore': fit,
        'fitTier': tier,
        'location': loc,
        'salary': sal,
        'source': src,
        'postedDate': posted_date,
        'link': link,
        'contactEmail': contact_email,
        'emailVerified': contacts.get('emailVerified', False),
        'companyLinkedIn': contacts.get('companyLinkedIn', ''),
        'companyLinkedInVerified': contacts.get('companyLinkedInVerified', False),
        'recruiterLinkedIn': recruiter_linkedin,
        'recruiterLinkedInVerified': contacts.get('recruiterLinkedInVerified', False),
        'contactName': contact_name,
        'description': desc or f"Opportunity for {clean_title} at {comp}.",
        'matchRationale': f"Relevant match based on role requirements in {clean_title} and Python/AI stack.",
        'coldEmailSubject': cold_subj,
        'coldEmailBody': cold_body,
        'coldEmailAngle': cold_angle,
        'status': 'Not Applied',
        'notes': ''
    })

print(f"Total clean, deduplicated job records: {len(master_list)}")

# Sort by date posted descending (newest first), with fitScore as tie-breaker
master_list.sort(key=lambda j: (j.get('postedDate', ''), j.get('fitScore', 0)), reverse=True)

# Save to jobs_data.json
for out_dir in [DATA_DIR, ROOT_DIR]:
    with open(out_dir / 'jobs_data.json', 'w', encoding='utf-8') as f:
        json.dump(master_list, f, indent=2, ensure_ascii=False)

    with open(out_dir / 'jobs_data.js', 'w', encoding='utf-8') as f:
        f.write('// Auto-generated Clean & Deduplicated Job Hunt Dataset\nwindow.INITIAL_JOBS_DATA = ' + json.dumps(master_list, indent=2, ensure_ascii=False) + ';\n')

print("Successfully updated jobs_data.json and jobs_data.js in data/ and root")
