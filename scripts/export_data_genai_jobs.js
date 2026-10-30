const fs = require('fs');
const XLSX = require('./xlsx.full.min.js');

// 1. Read raw Apify scraped jobs
const rawJobs = JSON.parse(fs.readFileSync('apify_dataset_196.json', 'utf8'));

// Target role regexes
const targetRoleRegex = /\b(data\s+engineer|data\s+scientist|data\s+science|data\s+analyst|data\s+analytics|big\s+data|gen\s*ai|generative\s+ai|ai\s*\/??\s*ml|ml\s*\/??\s*ai|machine\s+learning|artificial\s+intelligence|ai\s+engineer|ml\s+engineer|nlp\s+engineer|llm|deep\s+learning|computer\s+vision|ai\s+intern|ml\s+intern|data\s+intern|ai\s+agent|applied\s+scientist)\b/i;

// Exclude generic software engineer roles without data/AI context
const genericExcludeRegex = /^(software engineer|software developer|backend developer|frontend developer|full stack developer|java developer|c\+\+ developer|qa engineer|test engineer|devops engineer|product manager|scrum master|business analyst)$/i;

const locRegex = /(bangalore|bengaluru|noida|greater noida)/i;

const rows = [];
const seen = new Set();

rawJobs.forEach(job => {
  const title = (job.title || '').trim();
  const company = (job.companyName || '').trim();
  let location = (job.location || '').trim();
  const scrapingLoc = (job.scrapingInfo && job.scrapingInfo.location) || '';

  // Filter: Direct title match for data, genai, aiml
  if (!targetRoleRegex.test(title)) return;
  if (genericExcludeRegex.test(title)) return;

  // Filter: Bangalore + Noida
  const isBangalore = locRegex.test(location) || locRegex.test(scrapingLoc);
  if (!isBangalore) return;

  // Normalize location
  if (/bangalore|bengaluru/i.test(location) || /bangalore|bengaluru/i.test(scrapingLoc)) {
    location = location.includes('Karnataka') ? location : 'Bengaluru, Karnataka, India';
  } else if (/noida/i.test(location) || /noida/i.test(scrapingLoc)) {
    location = location.includes('Uttar Pradesh') ? location : 'Noida, Uttar Pradesh, India';
  }

  // Deduplicate
  const dedupKey = `${company.toLowerCase()}_${title.toLowerCase()}`;
  if (seen.has(dedupKey)) return;
  seen.add(dedupKey);

  // Clean posted date
  let postedDate = job.publishedAt || job.postedTime || '';
  if (job.publishedAt && job.postedTime) {
    postedDate = `${job.publishedAt} (${job.postedTime})`;
  } else if (job.publishedAt) {
    postedDate = job.publishedAt;
  } else if (job.postedTime) {
    postedDate = job.postedTime;
  }

  const applyLink = job.applyUrl || job.jobUrl || '';

  rows.push({
    "Job Title": title,
    "Company": company,
    "Location": location,
    "Posted Date": postedDate,
    "Apply Link": applyLink
  });
});

console.log(`Filtered ${rows.length} high-signal Data, GenAI, and AI/ML roles in Bangalore + Noida.`);

// Create Excel workbook
const wb = XLSX.utils.book_new();
const ws = XLSX.utils.json_to_sheet(rows);

// Set column widths matching the exact requested columns
ws['!cols'] = [
  { wch: 38 }, // Job Title
  { wch: 32 }, // Company
  { wch: 30 }, // Location
  { wch: 24 }, // Posted Date
  { wch: 55 }  // Apply Link
];

XLSX.utils.book_append_sheet(wb, ws, "Data_GenAI_AIML_Jobs");

const outputFile = 'LinkedIn_Data_GenAI_AIML_Jobs_Bangalore_Noida.xlsx';
const buf = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });
fs.writeFileSync(outputFile, buf);
console.log(`Generated spreadsheet: ${outputFile} (${rows.length} rows)`);

// Also save filtered JSON for inspectability
fs.writeFileSync('filtered_data_jobs.json', JSON.stringify(rows, null, 2));
