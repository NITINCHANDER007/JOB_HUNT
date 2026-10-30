# Job Hunt Intelligence & Auto-Apply Platform

An AI-curated job application dashboard, cold outreach generator, and automated application assistant with verified contact intelligence, real-time multi-platform job sync (LinkedIn, Indeed, Naukri), resume-based fit scoring, and Excel export.

---

## 🌟 Key Features

1. **Multi-Platform Authentic Feed:**
   - 185+ active opportunities across LinkedIn, Indeed, Naukri, and direct company career portals.
   - Preserves authentic publication dates (no fake repost dates).
   - Automated periodic background crawler syncing fresh opportunities every 4 hours.
   - Sliding 30-day expiration auditor archiving closed/expired roles.

2. **Resume Upload & Fit-Ranking Engine:**
   - Ingests `.pdf`, `.docx`, and `.txt` resumes directly from the header or the Resume Match Hub.
   - Extracts 35+ technical skills, tools, and candidate domain inclinations via `resume_matcher.py`.
   - Re-ranks opportunities instantly with highest fit roles first (e.g. 98% match).
   - Displays matched skills badge on every card and table row: e.g. `🎯 Matched: Python, Generative AI, RAG, FastAPI`.
   - Includes quick-load button: `⚡ Use Nitin's Resume` for instant testing.

3. **Interactive Role Slicer & Search Box:**
   - Visual Role Slicer bar with real-time counters:
     - `All Roles` (185)
     - `🤖 AI & GenAI`
     - `🧠 Machine Learning`
     - `📊 Data Scientist`
     - `⚙️ Data Engineer`
     - `🐍 Python & Backend`
     - `🎓 Internships`
   - Preserves active resume fit ranking within any selected role slice.
   - Live debounced keyword search box.

4. **Multi-Sheet Standardized Excel Export:**
   - Multi-sheet `.xlsx` and matching `.csv` downloads:
     - **Sheet 1 (`Jobs`):** `Job Title`, `Company`, `Location`, `Posted Date` (`YYYY-MM-DD`), `Apply Link` (clickable hyperlink displaying "Apply").
     - **Sheet 2 (`Resume Tips`):** 15 targeted resume tailoring actions (`ADD` & `REMOVE`) tailored for Data Engineer, GenAI, and ML applications.

5. **Verified Company & Recruiter Intelligence:**
   - Verified official company LinkedIn pages.
   - Direct fallback to LinkedIn Companies filter for unverified brands.
   - Separate recruiter search badge directing to LinkedIn People search filter without fabricating unverified profile links.

---

## 📁 Project Directory Structure

```text
job_hunt/
│
├── index.html                           # Web dashboard UI
├── styles.css                           # Modern dashboard design & dark mode styles
├── app.js                               # Frontend app logic, filtering & SheetJS exporter
├── apply_auto.js                        # Auto-apply frontend module
├── xlsx.full.min.js                     # Local SheetJS library
├── test_form.html                       # Demo application form for safe testing
├── run_app.py                           # Simple lightweight dashboard launcher
├── run_tests.py                         # Master test runner (executes all 9 test suites)
│
├── auto_apply_server.py                 # FastAPI automation backend, crawler API & live stream
├── resume_matcher.py                    # NLP skill extractor & resume fit ranking engine
├── apply_history.py                     # SQLite application history tracker
├── apply_history.db                     # Application history database
├── candidate_profile.py                 # Candidate profile manager & validation
├── profile_config.json                  # Candidate profile configuration
├── Nitin_resume.pdf                     # Candidate resume PDF
├── resume_text.txt                      # Plaintext resume for NLP processing
├── requirements_auto_apply.txt          # Python backend dependencies
│
├── apply_engine/                        # Form detection & automation engine
│   ├── apply_session.py                 # Application lifecycle manager
│   ├── base_handler.py                  # Abstract base class for site handlers
│   ├── handler_registry.py              # Site pattern matcher and dispatcher
│   └── handlers/                        # Site-specific application handlers
│
├── data/                                # Datasets & job feeds
│   ├── jobs_data.js                     # Curated jobs (frontend dataset)
│   ├── jobs_data.json                   # Curated jobs (backend JSON)
│   ├── incoming_pool.js                 # Candidate pool jobs (frontend stream)
│   ├── incoming_pool.json               # Candidate pool jobs (backend JSON)
│   ├── archived_jobs.json               # Pruned expired / stale opportunities
│   └── apify_dataset_196.json           # Scraped master dataset
│
├── scripts/                             # Scraping & dataset enrichment pipelines
│   ├── periodic_job_sync.py             # Multi-source periodic crawler (4-hour loop / sync-now)
│   ├── verify_job_availability.py       # Expiration & stale job pruning auditor
│   ├── build_dataset.py                 # Main dataset builder & enrichment pipeline
│   ├── build_multiplatform_dataset.py   # Multi-platform aggregator
│   ├── generate_excel.js                # Standardized 2-sheet Excel generator
│   └── generate_incoming_pool.py        # Pool generator with authentic timestamps
│
├── exports/                             # Generated reports & Excel exports
│   ├── Job_Hunt_Companies_Export.xlsx
│   ├── LinkedIn_Data_GenAI_AIML_Jobs_Bangalore_Noida.xlsx
│   ├── cold_emails.md
│   └── job_matches.md
│
└── tests/                               # Automated test suites
    ├── dashboard_test.py                # Dashboard HTTP & static asset verification
    ├── smoke_test.py                    # Smoke tests for profile & apply engine
    ├── api_test.py                      # Auto-apply FastAPI endpoint test suite
    ├── test_company_and_recruiter_links.py # Link audit & separation test
    ├── test_recruiter_links.py          # Recruiter URL verification test
    ├── test_contact_clicks.py           # E2E contact link interaction tests
    ├── test_refresh_live_jobs.py        # Live refresh & authentic date test
    ├── test_excel_export_format.py      # Multi-sheet Excel download format test
    ├── test_resume_upload_and_role_slicer.py # Resume upload & Role Slicer Playwright test
    └── test_resume_matcher.py           # NLP skill matcher & ranking unit test
```

---

## 🚀 Running the Project

### 1. Start the Backend Server & Dashboard
```bash
python -m uvicorn auto_apply_server:app --host 127.0.0.1 --port 5000
```
Then open: **http://127.0.0.1:5000/index.html**

### 2. Run All 9 Automated Tests
```bash
python run_tests.py
```
This executes all 9 automated test suites across the API, frontend, link verification, Excel downloads, and the resume fit ranking engine.
