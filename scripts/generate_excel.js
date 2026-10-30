const fs = require('fs');
const path = require('path');
const XLSX = require(path.join(__dirname, '../xlsx.full.min.js'));

// Load jobs data
const jobs = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/jobs_data.json'), 'utf8'));

// Format strictly matching requested columns: Job Title, Company, Location, Posted Date, Apply Link
const rows = jobs.map((job) => {
  let pDate = "2026-10-28";
  if (job.postedDate && typeof job.postedDate === 'string') {
    pDate = job.postedDate.trim().slice(0, 10);
  }
  return {
    "Job Title": job.title || "N/A",
    "Company": job.company || "N/A",
    "Location": job.location || "India",
    "Posted Date": pDate,
    "Apply Link": "Apply"
  };
});

const wb = XLSX.utils.book_new();
const wsJobs = XLSX.utils.json_to_sheet(rows);

// Attach clickable hyperlinks
jobs.forEach((job, idx) => {
  const cellRef = `E${idx + 2}`;
  if (wsJobs[cellRef] && job.link) {
    wsJobs[cellRef].l = { Target: job.link, Tooltip: `Apply at ${job.company}` };
  }
});

wsJobs['!cols'] = [
  { wch: 42 },  // Job Title
  { wch: 28 },  // Company
  { wch: 35 },  // Location
  { wch: 15 },  // Posted Date
  { wch: 14 }   // Apply Link
];

XLSX.utils.book_append_sheet(wb, wsJobs, "Jobs");

// Sheet 2: Resume Tips
const recommendations = [
  { Action: "ADD", Recommendation: "Azure/AWS AI + cloud data stack line: Azure OpenAI, Azure AI Search, Azure Data Factory, BigQuery (only what you have actually used or will genuinely learn before applying)" },
  { Action: "ADD", Recommendation: "Orchestration/ETL tools: Airflow, dbt, PySpark/Spark, Databricks, Kafka, plus data warehouse/data modelling (star schema, ETL vs ELT)" },
  { Action: "ADD", Recommendation: "GenAI depth: LangGraph/agents, function calling, structured outputs, chunking/embeddings, guardrails, and LLM evaluation (hallucination rate, task success)" },
  { Action: "ADD", Recommendation: "Deep learning frameworks: PyTorch or TensorFlow (named in many DS/AI JDs)" },
  { Action: "ADD", Recommendation: "CI/CD (GitHub Actions) and testing (pytest), monitoring/MLOps wording" },
  { Action: "ADD", Recommendation: "Metrics on every bullet: rows processed, latency, query speedup %, F1/ROC-AUC numbers, users served" },
  { Action: "ADD", Recommendation: "Dashboards/BI: Power BI or Tableau, plus time-series forecasting and A/B testing for DS/analyst roles" },
  { Action: "ADD", Recommendation: "Separate 'Cloud & Deployment' line for AWS/Azure services used; deploy one project (e.g., Travel Concierge or Fraud API) on AWS and link it" },
  { Action: "ADD", Recommendation: "GitHub/portfolio links for each project" },
  { Action: "REMOVE", Recommendation: "Class 12 percentage line and school name (keep B.Tech only)" },
  { Action: "REMOVE", Recommendation: "'Core Subjects' skills line (DSA, DBMS, CN, OS) - move DSA/System Design into one short mention or drop" },
  { Action: "REMOVE", Recommendation: "Repeated phrase 'AI-ready' across all three internships (reads as filler) - replace with concrete outputs" },
  { Action: "REMOVE", Recommendation: "Buzzword verbs 'Architected'/'Engineered' where scope was small; use plain verbs plus numbers" },
  { Action: "REMOVE", Recommendation: "Generic 'Statistics, Feature Engineering, Model Evaluation' in skills - show them in project bullets instead" },
  { Action: "REMOVE", Recommendation: "The multi-role objective sentence 'Seeking opportunities in...' - tailor a one-line headline per application (Data Engineer vs GenAI vs ML)" }
];

const wsRecs = XLSX.utils.json_to_sheet(recommendations);
wsRecs['!cols'] = [
  { wch: 12 },
  { wch: 95 }
];
XLSX.utils.book_append_sheet(wb, wsRecs, "Resume Tips");

const outputFile = path.join(__dirname, '../exports/Job_Hunt_Companies_Export.xlsx');
const buf = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });
fs.writeFileSync(outputFile, buf);
console.log(`Generated ${outputFile} with ${jobs.length} roles and ${recommendations.length} action recommendations.`);
