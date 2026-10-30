import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from resume_matcher import extract_text_from_pdf_bytes, score_all_jobs

def test_matcher():
    with open("Nitin_resume.pdf", "rb") as f:
        pdf_bytes = f.read()

    text = extract_text_from_pdf_bytes(pdf_bytes)
    assert len(text) > 500, "Resume text must be extracted"

    with open("data/jobs_data.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)

    result = score_all_jobs(jobs, text)
    print("Candidate:", result["profile"]["name"])
    print("Skills found:", len(result["profile"]["skills"]))
    print("Sample skills:", result["profile"]["skills"][:10])
    print("Total jobs scored:", result["total_jobs"])
    print("High matches:", result["high_matches"])

    print("\nTop 5 ranked jobs:")
    for j in result["jobs"][:5]:
        matched = ", ".join(j["matchedSkills"])
        print(f"  [{j['resumeMatchScore']}%] {j['company']} - {j['title']} (Matched: {matched})")

    assert result["total_jobs"] == len(jobs)
    assert result["jobs"][0]["resumeMatchScore"] >= result["jobs"][-1]["resumeMatchScore"]
    print("\nResume matcher test PASSED!")

if __name__ == "__main__":
    test_matcher()
