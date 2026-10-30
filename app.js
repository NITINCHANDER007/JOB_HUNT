// Job Hunt Intelligence & Excel Export Application
// Powered by SheetJS (XLSX)

(function () {
  'use strict';

  // 1. Data Store & State Initialization
  const STORAGE_KEY = 'job_hunt_tracker_store_v1';
  const DYNAMIC_JOBS_KEY = 'job_hunt_dynamic_new_jobs_v1';
  const POOL_INDEX_KEY = 'job_hunt_pool_index_v1';
  const EXACT_JOB_DATES = {
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
  };
  let jobs = [];
  let selectedIds = new Set();
  let currentView = 'table';
  let activeModalJob = null;

  const filters = {
    search: '',
    roleCategory: 'all',
    tier: 'all',
    location: 'all',
    source: 'all',
    status: 'all',
    sort: 'date-desc'
  };

  // DOM Elements Cache
  const searchInput = document.getElementById('searchInput');
  const searchClear = document.getElementById('searchClear');
  const viewTableBtn = document.getElementById('viewTableBtn');
  const viewGridBtn = document.getElementById('viewGridBtn');
  const tierFilterPills = document.getElementById('tierFilterPills');
  const locationFilter = document.getElementById('locationFilter');
  const sourceFilter = document.getElementById('sourceFilter');
  const statusFilter = document.getElementById('statusFilter');
  const sortSelect = document.getElementById('sortSelect');

  // Resume Hub Elements
  const btnHeaderUploadResume = document.getElementById('btnHeaderUploadResume');
  const btnHubUploadResume = document.getElementById('btnHubUploadResume');
  const resumeFileInput = document.getElementById('resumeFileInput');
  const resumeHubCard = document.getElementById('resumeHubCard');
  const resumeHubInactive = document.getElementById('resumeHubInactive');
  const resumeHubActive = document.getElementById('resumeHubActive');
  const activeResumeName = document.getElementById('activeResumeName');
  const activeResumeMeta = document.getElementById('activeResumeMeta');
  const activeResumeSkillsList = document.getElementById('activeResumeSkillsList');
  const btnChangeResume = document.getElementById('btnChangeResume');
  const btnResetResumeOrder = document.getElementById('btnResetResumeOrder');
  const btnLoadDefaultResume = document.getElementById('btnLoadDefaultResume');

  // Role Slicer Elements
  const roleSlicerPills = document.getElementById('roleSlicerPills');
  const slicerCountAll = document.getElementById('slicerCountAll');
  const slicerCountAi = document.getElementById('slicerCountAi');
  const slicerCountMl = document.getElementById('slicerCountMl');
  const slicerCountDs = document.getElementById('slicerCountDs');
  const slicerCountDe = document.getElementById('slicerCountDe');
  const slicerCountBackend = document.getElementById('slicerCountBackend');
  const slicerCountIntern = document.getElementById('slicerCountIntern');
  
  const jobsTableBody = document.getElementById('jobsTableBody');
  const tableViewSection = document.getElementById('tableViewSection');
  const cardsViewSection = document.getElementById('cardsViewSection');
  const emptyState = document.getElementById('emptyState');
  const selectAllCheckbox = document.getElementById('selectAllCheckbox');

  // Stats Elements
  const statTotalJobs = document.getElementById('statTotalJobs');
  const statHighFit = document.getElementById('statHighFit');
  const statColdEmails = document.getElementById('statColdEmails');
  const statTracked = document.getElementById('statTracked');

  // Selection Bar Elements
  const selectionBar = document.getElementById('selectionBar');
  const selectedCounter = document.getElementById('selectedCounter');
  const btnExportSelected = document.getElementById('btnExportSelected');
  const btnBulkStatus = document.getElementById('btnBulkStatus');
  const btnDeselectAll = document.getElementById('btnDeselectAll');

  // Export Dropdown Elements
  const btnExcelMain = document.getElementById('btnExcelMain');
  const exportDropdown = document.getElementById('exportDropdown');
  const exportAllExcel = document.getElementById('exportAllExcel');
  const exportFilteredExcel = document.getElementById('exportFilteredExcel');
  const exportSelectedExcel = document.getElementById('exportSelectedExcel');
  const exportCsv = document.getElementById('exportCsv');
  const copyJsonData = document.getElementById('copyJsonData');
  const dropdownAllCount = document.getElementById('dropdownAllCount');
  const dropdownFilteredCount = document.getElementById('dropdownFilteredCount');
  const dropdownSelectedCount = document.getElementById('dropdownSelectedCount');

  // Modal Elements
  const detailModal = document.getElementById('detailModal');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalCompanyName = document.getElementById('modalCompanyName');
  const modalRoleTitle = document.getElementById('modalRoleTitle');
  const modalFitScore = document.getElementById('modalFitScore');
  const modalFitTier = document.getElementById('modalFitTier');
  const modalSalary = document.getElementById('modalSalary');
  const modalSource = document.getElementById('modalSource');
  const modalRationale = document.getElementById('modalRationale');
  const modalApplyLink = document.getElementById('modalApplyLink');
  const modalSwitchToEmailBtn = document.getElementById('modalSwitchToEmailBtn');
  const modalEmailAngle = document.getElementById('modalEmailAngle');
  const modalEmailSubject = document.getElementById('modalEmailSubject');
  const modalEmailBody = document.getElementById('modalEmailBody');
  const btnCopyEmail = document.getElementById('btnCopyEmail');
  const btnMailto = document.getElementById('btnMailto');
  const modalFullDesc = document.getElementById('modalFullDesc');
  const modalStatusSelect = document.getElementById('modalStatusSelect');
  const modalNotesText = document.getElementById('modalNotesText');
  const btnSaveNotes = document.getElementById('btnSaveNotes');
  const modalRecruiterName = document.getElementById('modalRecruiterName');
  const modalContactEmail = document.getElementById('modalContactEmail');
  const modalCompanyLinkedIn = document.getElementById('modalCompanyLinkedIn');
  const modalRecruiterLinkedIn = document.getElementById('modalRecruiterLinkedIn');
  const btnCopyContactEmail = document.getElementById('btnCopyContactEmail');
  const modalOverviewContactCard = document.getElementById('modalOverviewContactCard');
  const modalOverviewContactName = document.getElementById('modalOverviewContactName');
  const modalOverviewEmail = document.getElementById('modalOverviewEmail');
  const modalOverviewCompanyLinkedIn = document.getElementById('modalOverviewCompanyLinkedIn');
  const modalOverviewRecruiterLinkedIn = document.getElementById('modalOverviewRecruiterLinkedIn');
  const modalOverviewLinkedIn = document.getElementById('modalOverviewLinkedIn');

  // Add Job Modal
  const btnAddCompany = document.getElementById('btnAddCompany');
  const addCompanyModal = document.getElementById('addCompanyModal');
  const addModalCloseBtn = document.getElementById('addModalCloseBtn');
  const btnAddCancel = document.getElementById('btnAddCancel');
  const addJobForm = document.getElementById('addJobForm');

  // Toast Container
  const toastContainer = document.getElementById('toastContainer');

  // 2. Initialize Data from window.INITIAL_JOBS_DATA and LocalStorage
  function initData() {
    const rawData = window.INITIAL_JOBS_DATA || [];
    let savedOverrides = {};
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        savedOverrides = JSON.parse(stored);
      }
    } catch (e) {
      console.warn('LocalStorage error:', e);
    }

    // Merge overrides (e.g. status, notes, or custom added jobs) and enforce exact postedDate
    jobs = rawData.map(item => {
      const override = savedOverrides[item.id] || {};
      const exactDate = item.postedDate || EXACT_JOB_DATES[item.id] || '2026-10-24 09:30:00';
      return {
        ...item,
        postedDate: exactDate,
        status: override.status || item.status || 'Not Applied',
        notes: override.notes !== undefined ? override.notes : item.notes || ''
      };
    });

    // Check for custom added jobs stored separately
    if (savedOverrides.__custom_jobs && Array.isArray(savedOverrides.__custom_jobs)) {
      savedOverrides.__custom_jobs.forEach(customJob => {
        if (!jobs.some(j => j.id === customJob.id)) {
          jobs.push(customJob);
        }
      });
    }

    // Clear any legacy synthetic dynamic jobs so feed remains 100% authentic
    try {
      localStorage.removeItem(DYNAMIC_JOBS_KEY);
    } catch {}

    updateStats();
    render();
  }

  // Save changes to localStorage
  function persistJobChanges(jobId, updates) {
    try {
      let savedOverrides = {};
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        savedOverrides = JSON.parse(stored);
      }
      savedOverrides[jobId] = {
        ...(savedOverrides[jobId] || {}),
        ...updates
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(savedOverrides));
    } catch (e) {
      console.warn('Could not save to localStorage:', e);
    }
  }

  function saveCustomJob(job) {
    try {
      let savedOverrides = {};
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        savedOverrides = JSON.parse(stored);
      }
      if (!savedOverrides.__custom_jobs) {
        savedOverrides.__custom_jobs = [];
      }
      savedOverrides.__custom_jobs.push(job);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(savedOverrides));
    } catch (e) {
      console.warn('Could not save custom job:', e);
    }
  }

  // Synchronize live job feed across platforms (LinkedIn, Indeed, Naukri, Direct)
  async function syncLiveFeed(isManualClick = false) {
    let syncInfo = null;

    // 1. Query server sync endpoint
    try {
      const res = await fetch('/api/jobs/sync', { cache: 'no-store' });
      if (res.ok) {
        syncInfo = await res.json();
      }

      // If server has more active jobs than local memory, fetch latest dataset
      if (syncInfo && syncInfo.total_active && syncInfo.total_active > jobs.length) {
        const jobsRes = await fetch('/data/jobs_data.json', { cache: 'no-store' });
        if (jobsRes.ok) {
          const freshList = await jobsRes.json();
          if (Array.isArray(freshList) && freshList.length > 0) {
            jobs = freshList;
          }
        }
      }
    } catch {
      // Offline / static hosting fallback
    }

    // 2. Re-compute stats and render
    updateStats();
    render();

    const activeCount = syncInfo ? syncInfo.total_active : jobs.length;
    if (isManualClick) {
      showToast(`✓ Feed up to date • ${activeCount} active opportunities across LinkedIn, Indeed & Naukri`, 'success');
    }

    return syncInfo || { status: 'synced', total_active: activeCount };
  }

  // Alias for backward compatibility
  async function fetchNewJob(isManualClick = false) {
    return syncLiveFeed(isManualClick);
  }

  // 3. Filtering & Sorting
  function getFilteredJobs() {
    let result = jobs.filter(item => {
      // Search
      if (filters.search) {
        const query = filters.search.toLowerCase();
        const comp = (item.company || '').toLowerCase();
        const title = (item.title || '').toLowerCase();
        const loc = (item.location || '').toLowerCase();
        const desc = (item.description || '').toLowerCase();
        const why = (item.matchRationale || '').toLowerCase();
        if (!comp.includes(query) && !title.includes(query) && !loc.includes(query) && !desc.includes(query) && !why.includes(query)) {
          return false;
        }
      }

      // Role Category Slicer
      if (filters.roleCategory && filters.roleCategory !== 'all') {
        const titleLower = (item.title || '').toLowerCase();
        const descLower = (item.description || '').toLowerCase();
        const combined = `${titleLower} ${descLower}`;

        switch (filters.roleCategory) {
          case 'ai-genai':
            if (!['ai', 'genai', 'generative', 'llm', 'agentic', 'agent', 'artificial intelligence'].some(k => combined.includes(k))) {
              return false;
            }
            break;
          case 'ml':
            if (!['ml', 'machine learning', 'deep learning', 'computer vision', 'nlp', 'scikit'].some(k => combined.includes(k))) {
              return false;
            }
            break;
          case 'ds':
            if (!['data scientist', 'data science', 'analytics'].some(k => combined.includes(k))) {
              return false;
            }
            break;
          case 'de':
            if (!['data engineer', 'etl', 'databricks', 'spark', 'pyspark', 'data platform', 'data pipeline'].some(k => combined.includes(k))) {
              return false;
            }
            break;
          case 'backend':
            if (!['python', 'backend', 'developer', 'software engineer', 'fastapi', 'flask', 'django'].some(k => combined.includes(k))) {
              return false;
            }
            break;
          case 'intern':
            if (!['intern', 'internship', 'trainee', 'fresher', 'entry level', 'graduate'].some(k => combined.includes(k))) {
              return false;
            }
            break;
        }
      }

      // Tier
      if (filters.tier !== 'all' && item.fitTier !== filters.tier) {
        return false;
      }

      // Location
      if (filters.location !== 'all') {
        const loc = (item.location || '').toLowerCase();
        if (filters.location === 'delhi' && !(loc.includes('delhi') || loc.includes('noida') || loc.includes('gurgaon') || loc.includes('ncr'))) {
          return false;
        }
        if (filters.location === 'bengaluru' && !(loc.includes('bengaluru') || loc.includes('bangalore'))) {
          return false;
        }
        if (filters.location === 'remote' && !(loc.includes('remote') || loc.includes('hybrid'))) {
          return false;
        }
        if (filters.location === 'hyderabad' && !loc.includes('hyderabad')) {
          return false;
        }
        if (filters.location === 'pune' && !loc.includes('pune')) {
          return false;
        }
        if (filters.location === 'mumbai' && !(loc.includes('mumbai') || loc.includes('thane'))) {
          return false;
        }
      }

      // Source
      if (filters.source !== 'all') {
        const src = (item.source || '').toLowerCase();
        if (filters.source === 'LinkedIn' && !src.includes('linkedin')) return false;
        if (filters.source === 'Indeed' && !src.includes('indeed')) return false;
        if (filters.source === 'Naukri' && !src.includes('naukri')) return false;
        if (filters.source === 'Direct' && (src.includes('linkedin') || src.includes('indeed') || src.includes('naukri'))) return false;
      }

      // Status
      if (filters.status !== 'all' && item.status !== filters.status) {
        return false;
      }

      return true;
    });

    // Sorting
    result.sort((a, b) => {
      switch (filters.sort) {
        case 'date-desc': {
          const dateDiff = (b.postedDate || '').localeCompare(a.postedDate || '');
          if (dateDiff !== 0) return dateDiff;
          return (b.fitScore || 0) - (a.fitScore || 0);
        }
        case 'date-asc': {
          const dateDiff = (a.postedDate || '').localeCompare(b.postedDate || '');
          if (dateDiff !== 0) return dateDiff;
          return (b.fitScore || 0) - (a.fitScore || 0);
        }
        case 'fit-desc':
          return (b.fitScore || 0) - (a.fitScore || 0);
        case 'fit-asc':
          return (a.fitScore || 0) - (b.fitScore || 0);
        case 'company-asc':
          return (a.company || '').localeCompare(b.company || '');
        case 'title-asc':
          return (a.title || '').localeCompare(b.title || '');
        default: {
          const dateDiff = (b.postedDate || '').localeCompare(a.postedDate || '');
          if (dateDiff !== 0) return dateDiff;
          return (b.fitScore || 0) - (a.fitScore || 0);
        }
      }
    });

    return result;
  }

  // 4. Update KPI Metrics
  function updateStats() {
    statTotalJobs.textContent = jobs.length;
    const highFitCount = jobs.filter(j => (j.fitScore || 0) >= 75).length;
    statHighFit.textContent = highFitCount;
    const readyEmailsCount = jobs.filter(j => j.coldEmailBody && j.coldEmailBody.length > 30).length;
    statColdEmails.textContent = readyEmailsCount;
    const inProgressCount = jobs.filter(j => j.status && j.status !== 'Not Applied' && j.status !== 'Rejected').length;
    statTracked.textContent = inProgressCount;

    // Update Role Slicer Counts
    if (slicerCountAll) slicerCountAll.textContent = jobs.length;
    if (slicerCountAi) {
      slicerCountAi.textContent = jobs.filter(j => {
        const c = `${(j.title || '').toLowerCase()} ${(j.description || '').toLowerCase()}`;
        return ['ai', 'genai', 'generative', 'llm', 'agentic', 'agent', 'artificial intelligence'].some(k => c.includes(k));
      }).length;
    }
    if (slicerCountMl) {
      slicerCountMl.textContent = jobs.filter(j => {
        const c = `${(j.title || '').toLowerCase()} ${(j.description || '').toLowerCase()}`;
        return ['ml', 'machine learning', 'deep learning', 'computer vision', 'nlp', 'scikit'].some(k => c.includes(k));
      }).length;
    }
    if (slicerCountDs) {
      slicerCountDs.textContent = jobs.filter(j => {
        const c = `${(j.title || '').toLowerCase()} ${(j.description || '').toLowerCase()}`;
        return ['data scientist', 'data science', 'analytics'].some(k => c.includes(k));
      }).length;
    }
    if (slicerCountDe) {
      slicerCountDe.textContent = jobs.filter(j => {
        const c = `${(j.title || '').toLowerCase()} ${(j.description || '').toLowerCase()}`;
        return ['data engineer', 'etl', 'databricks', 'spark', 'pyspark', 'data platform', 'data pipeline'].some(k => c.includes(k));
      }).length;
    }
    if (slicerCountBackend) {
      slicerCountBackend.textContent = jobs.filter(j => {
        const c = `${(j.title || '').toLowerCase()} ${(j.description || '').toLowerCase()}`;
        return ['python', 'backend', 'developer', 'software engineer', 'fastapi', 'flask', 'django'].some(k => c.includes(k));
      }).length;
    }
    if (slicerCountIntern) {
      slicerCountIntern.textContent = jobs.filter(j => {
        const c = `${(j.title || '').toLowerCase()} ${(j.description || '').toLowerCase()}`;
        return ['intern', 'internship', 'trainee', 'fresher', 'entry level', 'graduate'].some(k => c.includes(k));
      }).length;
    }
  }

  // 5. Render Core UI
  function render() {
    const filtered = getFilteredJobs();

    // Update Dropdown counts
    dropdownAllCount.textContent = jobs.length;
    dropdownFilteredCount.textContent = filtered.length;
    dropdownSelectedCount.textContent = selectedIds.size;
    if (selectedIds.size > 0) {
      exportSelectedExcel.removeAttribute('disabled');
      exportSelectedExcel.style.opacity = '1';
    } else {
      exportSelectedExcel.setAttribute('disabled', 'true');
      exportSelectedExcel.style.opacity = '0.6';
    }

    // Update Selection Bar
    if (selectedIds.size > 0) {
      selectionBar.classList.add('active');
      selectedCounter.textContent = selectedIds.size;
    } else {
      selectionBar.classList.remove('active');
    }

    // Toggle Empty State
    if (filtered.length === 0) {
      emptyState.style.display = 'block';
      tableViewSection.style.display = 'none';
      cardsViewSection.style.display = 'none';
      return;
    } else {
      emptyState.style.display = 'none';
      if (currentView === 'table') {
        tableViewSection.style.display = 'block';
        cardsViewSection.style.display = 'none';
      } else {
        tableViewSection.style.display = 'none';
        cardsViewSection.style.display = 'grid';
      }
    }

    // Update Select All Checkbox state
    const allVisibleSelected = filtered.every(j => selectedIds.has(j.id));
    const someVisibleSelected = filtered.some(j => selectedIds.has(j.id));
    selectAllCheckbox.checked = allVisibleSelected && filtered.length > 0;
    selectAllCheckbox.indeterminate = !allVisibleSelected && someVisibleSelected;

    // Render Table View
    jobsTableBody.innerHTML = '';
    filtered.forEach(job => {
      const tr = document.createElement('tr');
      if (selectedIds.has(job.id)) tr.classList.add('selected');

      const isHigh = job.fitScore >= 75;
      const isMed = job.fitScore >= 60 && job.fitScore < 75;
      const fitClass = isHigh ? 'fit-high' : (isMed ? 'fit-medium' : 'fit-stretch');

      tr.innerHTML = `
        <td class="col-check">
          <input type="checkbox" class="custom-checkbox row-checkbox" data-id="${job.id}" ${selectedIds.has(job.id) ? 'checked' : ''}>
        </td>
        <td class="col-score">
          <span class="fit-badge ${fitClass}">${job.fitScore}%</span>
        </td>
        <td class="col-company">
          <div class="company-cell">
            <div class="company-info">
              <div class="company-name">${escapeHtml(job.company)}</div>
            </div>
          </div>
        </td>
        <td class="col-role">
          <div style="font-weight: 600; color: #fff;">${escapeHtml(job.title)}</div>
          ${job.fitTier === 'High' ? '<span style="font-size: 0.72rem; color: #34d399;">★ Top Match</span>' : ''}
          ${(job.matchedSkills && job.matchedSkills.length > 0) ? `<div class="matched-skills-tag">🎯 Matched: ${job.matchedSkills.slice(0, 3).map(escapeHtml).join(', ')}</div>` : ''}
        </td>
        <td class="col-location">
          <div class="loc-tag">
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
            <span>${escapeHtml(job.location)}</span>
          </div>
        </td>
        <td class="col-salary">
          <span class="salary-tag">${escapeHtml(job.salary || 'Competitive')}</span>
        </td>
        <td class="col-date">
          <div class="date-tag">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
            <span>${escapeHtml(formatDate(job.postedDate, job.id))}</span>
            ${(job.isNew || isRecentlyPosted(job.postedDate)) ? '<span class="badge-new-live">NEW</span>' : ''}
          </div>
        </td>
        <td class="col-status">
          <select class="status-select status-select-cell ${getStatusClass(job.status)}" data-id="${job.id}">
            <option value="Not Applied" ${job.status === 'Not Applied' ? 'selected' : ''}>Not Applied</option>
            <option value="Cold Emailed" ${job.status === 'Cold Emailed' ? 'selected' : ''}>Cold Emailed</option>
            <option value="Applied" ${job.status === 'Applied' ? 'selected' : ''}>Applied</option>
            <option value="Interviewing" ${job.status === 'Interviewing' ? 'selected' : ''}>Interviewing</option>
            <option value="Offer" ${job.status === 'Offer' ? 'selected' : ''}>Offer</option>
            <option value="Rejected" ${job.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
          </select>
        </td>
        <td class="col-actions">
          <div class="action-group">
            <button class="btn-icon primary btn-open-modal" data-id="${job.id}" title="View details & match rationale">
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
            </button>
            <button class="btn-icon email btn-quick-email" data-id="${job.id}" title="Copy cold email pitch">
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
            </button>
            ${job.link ? `
              <a href="${escapeHtml(job.link)}" target="_blank" rel="noopener noreferrer" class="btn-icon" title="Open job application link">
                <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
              </a>
            ` : ''}
          </div>
        </td>
      `;
      jobsTableBody.appendChild(tr);
    });

    // Render Cards View
    cardsViewSection.innerHTML = '';
    filtered.forEach(job => {
      const card = document.createElement('div');
      card.className = 'job-card';

      const isHigh = job.fitScore >= 75;
      const isMed = job.fitScore >= 60 && job.fitScore < 75;
      const fitClass = isHigh ? 'fit-high' : (isMed ? 'fit-medium' : 'fit-stretch');
      const avatarLetter = (job.company || 'C').charAt(0).toUpperCase();

      card.innerHTML = `
        <div>
          <div class="card-top">
            <div class="card-company-header">
              <div class="company-avatar">${avatarLetter}</div>
              <div>
                <div style="font-weight: 700; color: #fff;">${escapeHtml(job.company)}</div>
                <span class="source-badge ${getSourceClass(job.source)}">${escapeHtml(job.source || 'Direct')}</span>
              </div>
            </div>
            <span class="fit-badge ${fitClass}">${job.fitScore}% Match</span>
          </div>

          <div class="card-title">${escapeHtml(job.title)}</div>
          ${(job.matchedSkills && job.matchedSkills.length > 0) ? `
            <div class="matched-skills-tag" style="margin-top: 6px;">
              <span>🎯 Matched:</span> ${job.matchedSkills.slice(0, 4).map(escapeHtml).join(' • ')}
            </div>
          ` : ''}

          <div class="card-meta" style="margin-top: 12px;">
            <div class="loc-tag">
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
              <span>${escapeHtml(job.location)}</span>
            </div>
            <div class="salary-tag">${escapeHtml(job.salary || 'Competitive Stipend')}</div>
            <div class="date-tag" style="font-size: 0.76rem;" title="Date Posted: ${escapeHtml(formatDate(job.postedDate, job.id))}">
              <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              <span>${escapeHtml(formatDate(job.postedDate, job.id))}</span>
              ${(job.isNew || isRecentlyPosted(job.postedDate)) ? '<span class="badge-new-live">NEW</span>' : ''}
            </div>
          </div>

          <div class="card-desc" style="margin-top: 12px;">
            ${escapeHtml(job.matchRationale || job.description || '')}
          </div>
        </div>

        <div class="card-bottom">
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
            ${job.contactEmail && isValidEmail(job.contactEmail) ? `
              <a href="mailto:${escapeHtml(job.contactEmail)}" class="contact-badge contact-email-badge" title="Send email to ${escapeHtml(job.contactEmail)}${job.emailVerified ? ' (Verified)' : ' (Unverified)'}" onclick="event.stopPropagation()">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                <span>${escapeHtml(job.contactEmail)}</span>
              </a>
            ` : ''}
            ${job.companyLinkedIn && job.companyLinkedInVerified && isValidUrl(job.companyLinkedIn) ? `
              <a href="${escapeHtml(job.companyLinkedIn)}" target="_blank" rel="noopener noreferrer" class="contact-badge contact-company-badge" title="Company LinkedIn: ${escapeHtml(job.company)}" onclick="event.stopPropagation()">
                <svg width="11" height="11" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v7.6h2.8v-7.6h-2.8M7.86 6.54a1.63 1.63 0 1 0 0 3.26 1.63 1.63 0 0 0 0-3.26z"/></svg>
                <span>Company LinkedIn</span>
              </a>
            ` : `
              <a href="${escapeHtml(getCompanyLinkedInUrl(job))}" target="_blank" rel="noopener noreferrer" class="contact-badge contact-company-search-badge" title="Find ${escapeHtml(job.company)} on LinkedIn" onclick="event.stopPropagation()">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Find Company on LinkedIn</span>
              </a>
            `}
            ${job.recruiterLinkedIn && job.recruiterLinkedInVerified && isValidUrl(job.recruiterLinkedIn) ? `
              <a href="${escapeHtml(job.recruiterLinkedIn)}" target="_blank" rel="noopener noreferrer" class="contact-badge contact-recruiter-badge" title="Recruiter LinkedIn: ${escapeHtml(job.contactName || job.company)}" onclick="event.stopPropagation()">
                <svg width="11" height="11" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v7.6h2.8v-7.6h-2.8M7.86 6.54a1.63 1.63 0 1 0 0 3.26 1.63 1.63 0 0 0 0-3.26z"/></svg>
                <span>Recruiter LinkedIn</span>
              </a>
            ` : `
              <a href="${escapeHtml(getRecruiterLinkedInUrl(job))}" target="_blank" rel="noopener noreferrer" class="contact-badge contact-recruiter-search-badge" title="Search LinkedIn People for ${escapeHtml(job.contactName || job.company)}" onclick="event.stopPropagation()">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Find Recruiter</span>
              </a>
            `}
          </div>
          <select class="status-select status-select-cell ${getStatusClass(job.status)}" data-id="${job.id}" style="width: 130px;">
            <option value="Not Applied" ${job.status === 'Not Applied' ? 'selected' : ''}>Not Applied</option>
            <option value="Cold Emailed" ${job.status === 'Cold Emailed' ? 'selected' : ''}>Cold Emailed</option>
            <option value="Applied" ${job.status === 'Applied' ? 'selected' : ''}>Applied</option>
            <option value="Interviewing" ${job.status === 'Interviewing' ? 'selected' : ''}>Interviewing</option>
            <option value="Offer" ${job.status === 'Offer' ? 'selected' : ''}>Offer</option>
          </select>

          <div class="action-group">
            <button class="btn-icon primary btn-open-modal" data-id="${job.id}" title="View details">
              <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
            </button>
            <button class="btn-icon email btn-quick-email" data-id="${job.id}" title="Copy email">
              <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
            </button>
            ${job.link ? `
              <a href="${escapeHtml(job.link)}" target="_blank" rel="noopener noreferrer" class="btn-icon" title="Apply">
                <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
              </a>
            ` : ''}
          </div>
        </div>
      `;
      cardsViewSection.appendChild(card);
    });
  }

  // Resume & Profile Optimization Recommendations
  const RESUME_RECOMMENDATIONS = [
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

  // 6. Excel (.xlsx) Generation & Export
  function exportToExcel(jobList, filenameLabel) {
    if (typeof XLSX === 'undefined') {
      showToast('❌ SheetJS (XLSX) library is loading. Please try in a few seconds.', 'error');
      return;
    }

    if (!jobList || jobList.length === 0) {
      showToast('⚠️ No company records to export.', 'warning');
      return;
    }

    // Format rows strictly matching: Job Title, Company, Location, Posted Date, Apply Link
    const excelRows = jobList.map((job) => {
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

    // Create a new workbook
    const wb = XLSX.utils.book_new();
    const wsJobs = XLSX.utils.json_to_sheet(excelRows);

    // Make "Apply" cell clickable with direct hyperlink to job application URL
    jobList.forEach((job, idx) => {
      const cellRef = `E${idx + 2}`;
      if (wsJobs[cellRef] && job.link) {
        wsJobs[cellRef].l = { Target: job.link, Tooltip: `Open application for ${job.title}` };
      }
    });

    // Optimal column widths
    wsJobs['!cols'] = [
      { wch: 42 },  // Job Title
      { wch: 28 },  // Company
      { wch: 35 },  // Location
      { wch: 15 },  // Posted Date
      { wch: 14 }   // Apply Link
    ];

    XLSX.utils.book_append_sheet(wb, wsJobs, "Jobs");

    // Sheet 2: Resume Tips
    const wsRecs = XLSX.utils.json_to_sheet(RESUME_RECOMMENDATIONS);
    wsRecs['!cols'] = [
      { wch: 12 },  // Action
      { wch: 95 }   // Recommendation
    ];
    XLSX.utils.book_append_sheet(wb, wsRecs, "Resume Tips");

    const today = new Date().toISOString().slice(0, 10);
    const cleanLabel = (filenameLabel || 'Job_Hunt_Opportunities').replace(/[^a-zA-Z0-9_-]/g, '_');
    const fileName = `${cleanLabel}_${today}.xlsx`;

    XLSX.writeFile(wb, fileName);
    showToast(`✅ Exported ${jobList.length} jobs to "${fileName}"!`, 'success');
  }

  // 7. CSV Export Fallback
  function exportToCsv(jobList, filenameLabel) {
    if (!jobList || jobList.length === 0) {
      showToast('⚠️ No records to export.', 'warning');
      return;
    }

    const escapeCsv = (str) => {
      if (str === null || str === undefined) return '""';
      const s = String(str).replace(/"/g, '""');
      return `"${s}"`;
    };

    const csvLines = [
      "Job Title,Company,Location,Posted Date,Apply Link"
    ];

    jobList.forEach((j) => {
      let pDate = "2026-10-28";
      if (j.postedDate && typeof j.postedDate === 'string') {
        pDate = j.postedDate.trim().slice(0, 10);
      }
      csvLines.push([
        escapeCsv(j.title),
        escapeCsv(j.company),
        escapeCsv(j.location),
        escapeCsv(pDate),
        "Apply"
      ].join(','));
    });

    // Append Recommendations section
    csvLines.push("");
    csvLines.push("Action,Recommendation");
    RESUME_RECOMMENDATIONS.forEach((rec) => {
      csvLines.push([
        escapeCsv(rec.Action),
        escapeCsv(rec.Recommendation)
      ].join(','));
    });

    const blob = new Blob([csvLines.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(filenameLabel || 'Job_Hunt_Opportunities').replace(/[^a-zA-Z0-9_-]/g, '_')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`✅ Exported CSV with ${jobList.length} records.`, 'success');
  }

  // 8. Event Handlers & User Interactions
  function setupEventListeners() {
    // Search with debounce
    let searchTimer = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimer);
      searchClear.style.display = e.target.value ? 'block' : 'none';
      searchTimer = setTimeout(() => {
        filters.search = e.target.value.trim();
        render();
      }, 150);
    });

    searchClear.addEventListener('click', () => {
      searchInput.value = '';
      filters.search = '';
      searchClear.style.display = 'none';
      render();
    });

    // View switcher
    viewTableBtn.addEventListener('click', () => {
      currentView = 'table';
      viewTableBtn.classList.add('active');
      viewGridBtn.classList.remove('active');
      render();
    });
    viewGridBtn.addEventListener('click', () => {
      currentView = 'grid';
      viewGridBtn.classList.add('active');
      viewTableBtn.classList.remove('active');
      render();
    });

    // Tier Pills
    tierFilterPills.addEventListener('click', (e) => {
      if (e.target.classList.contains('pill-btn')) {
        tierFilterPills.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        filters.tier = e.target.getAttribute('data-tier');
        render();
      }
    });

    // Location & Platform & Status Filters
    locationFilter.addEventListener('change', (e) => {
      filters.location = e.target.value;
      render();
    });
    sourceFilter.addEventListener('change', (e) => {
      filters.source = e.target.value;
      render();
    });
    statusFilter.addEventListener('change', (e) => {
      filters.status = e.target.value;
      render();
    });
    sortSelect.addEventListener('change', (e) => {
      filters.sort = e.target.value;
      render();
    });

    // Checkbox Selections
    selectAllCheckbox.addEventListener('change', (e) => {
      const filtered = getFilteredJobs();
      if (e.target.checked) {
        filtered.forEach(j => selectedIds.add(j.id));
      } else {
        filtered.forEach(j => selectedIds.delete(j.id));
      }
      render();
    });

    document.addEventListener('change', (e) => {
      // Row checkbox
      if (e.target.classList.contains('row-checkbox')) {
        const id = parseInt(e.target.getAttribute('data-id'), 10);
        if (e.target.checked) {
          selectedIds.add(id);
        } else {
          selectedIds.delete(id);
        }
        render();
      }

      // Inline status dropdown change
      if (e.target.classList.contains('status-select-cell')) {
        const id = parseInt(e.target.getAttribute('data-id'), 10);
        const newStatus = e.target.value;
        const job = jobs.find(j => j.id === id);
        if (job) {
          job.status = newStatus;
          persistJobChanges(id, { status: newStatus });
          e.target.className = `status-select status-select-cell ${getStatusClass(newStatus)}`;
          updateStats();
          showToast(`Updated "${job.company}" to "${newStatus}"`, 'info');
        }
      }
    });

    // Bulk selection bar actions
    btnDeselectAll.addEventListener('click', () => {
      selectedIds.clear();
      render();
    });

    btnBulkStatus.addEventListener('click', () => {
      if (selectedIds.size === 0) return;
      selectedIds.forEach(id => {
        const job = jobs.find(j => j.id === id);
        if (job) {
          job.status = 'Cold Emailed';
          persistJobChanges(id, { status: 'Cold Emailed' });
        }
      });
      updateStats();
      render();
      showToast(`Marked ${selectedIds.size} companies as "Cold Emailed"`, 'success');
    });

    btnExportSelected.addEventListener('click', () => {
      const selectedJobs = jobs.filter(j => selectedIds.has(j.id));
      exportToExcel(selectedJobs, 'Selected_Target_Companies');
    });

    // Export Dropdown Trigger
    btnExcelMain.addEventListener('click', (e) => {
      e.stopPropagation();
      exportDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!btnExcelMain.contains(e.target) && !exportDropdown.contains(e.target)) {
        exportDropdown.classList.remove('show');
      }
    });

    // Dropdown Items
    exportAllExcel.addEventListener('click', () => {
      exportDropdown.classList.remove('show');
      exportToExcel(jobs, 'All_Companies_Master_Export');
    });

    exportFilteredExcel.addEventListener('click', () => {
      exportDropdown.classList.remove('show');
      const filtered = getFilteredJobs();
      exportToExcel(filtered, 'Filtered_Companies_Export');
    });

    exportSelectedExcel.addEventListener('click', () => {
      exportDropdown.classList.remove('show');
      const selectedJobs = jobs.filter(j => selectedIds.has(j.id));
      exportToExcel(selectedJobs, 'Selected_Target_Companies');
    });

    exportCsv.addEventListener('click', () => {
      exportDropdown.classList.remove('show');
      const filtered = getFilteredJobs();
      exportToCsv(filtered, 'Job_Hunt_Companies_Export');
    });

    copyJsonData.addEventListener('click', () => {
      exportDropdown.classList.remove('show');
      const filtered = getFilteredJobs();
      navigator.clipboard.writeText(JSON.stringify(filtered, null, 2)).then(() => {
        showToast('📋 Copied JSON dataset to clipboard!', 'success');
      });
    });

    // Delegate row button clicks (Open Modal, Quick Email)
    document.addEventListener('click', (e) => {
      // Ensure contact badge/link clicks navigate naturally without triggering other actions
      const contactElem = e.target.closest('.contact-badge, .modal-contact-link, #modalContactEmail, #modalCompanyLinkedIn, #modalRecruiterLinkedIn, #modalOverviewEmail, #modalOverviewCompanyLinkedIn, #modalOverviewRecruiterLinkedIn, #modalOverviewLinkedIn');
      if (contactElem) {
        e.stopPropagation();
        return;
      }

      const modalBtn = e.target.closest('.btn-open-modal');
      if (modalBtn) {
        const id = parseInt(modalBtn.getAttribute('data-id'), 10);
        openDetailModal(id);
        return;
      }

      const emailBtn = e.target.closest('.btn-quick-email');
      if (emailBtn) {
        const id = parseInt(emailBtn.getAttribute('data-id'), 10);
        const job = jobs.find(j => j.id === id);
        if (job) {
          copyJobEmail(job);
        }
        return;
      }
    });

    // Modal Tabs
    const tabBtns = document.querySelectorAll('.modal-tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.getAttribute('data-tab');

        document.getElementById('tabOverview').style.display = tab === 'overview' ? 'block' : 'none';
        document.getElementById('tabEmail').style.display = tab === 'email' ? 'block' : 'none';
        document.getElementById('tabDesc').style.display = tab === 'desc' ? 'block' : 'none';
        document.getElementById('tabNotes').style.display = tab === 'notes' ? 'block' : 'none';
      });
    });

    modalSwitchToEmailBtn.addEventListener('click', () => {
      const emailTabBtn = document.querySelector('.modal-tab-btn[data-tab="email"]');
      if (emailTabBtn) emailTabBtn.click();
    });

    modalCloseBtn.addEventListener('click', () => {
      detailModal.classList.remove('show');
    });

    detailModal.addEventListener('click', (e) => {
      if (e.target === detailModal) detailModal.classList.remove('show');
    });

    // Copy Email from Modal
    btnCopyEmail.addEventListener('click', () => {
      if (!activeModalJob) return;
      const textToCopy = `Subject: ${activeModalJob.coldEmailSubject || ''}\n\n${activeModalJob.coldEmailBody || ''}`;
      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast('✉️ Cold email copied to clipboard!', 'success');
      });
    });

    // Save Notes from Modal
    btnSaveNotes.addEventListener('click', () => {
      if (!activeModalJob) return;
      const newStatus = modalStatusSelect.value;
      const newNotes = modalNotesText.value.trim();

      activeModalJob.status = newStatus;
      activeModalJob.notes = newNotes;

      persistJobChanges(activeModalJob.id, {
        status: newStatus,
        notes: newNotes
      });

      updateStats();
      render();
      showToast('💾 Application notes & status saved!', 'success');
    });

    // Add Job Modal
    btnAddCompany.addEventListener('click', () => {
      addCompanyModal.classList.add('show');
    });
    addModalCloseBtn.addEventListener('click', () => {
      addCompanyModal.classList.remove('show');
    });
    btnAddCancel.addEventListener('click', () => {
      addCompanyModal.classList.remove('show');
    });
    addCompanyModal.addEventListener('click', (e) => {
      if (e.target === addCompanyModal) addCompanyModal.classList.remove('show');
    });

    addJobForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const comp = document.getElementById('newCompany').value.trim();
      const title = document.getElementById('newTitle').value.trim();
      const loc = document.getElementById('newLocation').value.trim() || 'India / Remote';
      const sal = document.getElementById('newSalary').value.trim() || 'Competitive';
      const link = document.getElementById('newLink').value.trim();
      const fit = parseInt(document.getElementById('newFit').value, 10) || 80;
      const desc = document.getElementById('newDesc').value.trim() || 'Custom added opportunity.';

      const newJob = {
        id: jobs.length + 1000 + Math.floor(Math.random() * 900),
        company: comp,
        title: title,
        fitScore: fit,
        fitTier: fit >= 75 ? 'High' : (fit >= 60 ? 'Medium' : 'Stretch'),
        location: loc,
        salary: sal,
        source: 'Custom / Added',
        postedDate: new Date().toISOString().split('T')[0],
        link: link,
        description: desc,
        matchRationale: 'Manually added high-interest opportunity.',
        coldEmailSubject: `Application for ${title} | Nitin Chander`,
        coldEmailBody: `Hi ${comp} Team,\n\nI am writing to express my enthusiasm for the ${title} opportunity. With experience building Python data pipelines, RAG systems, and REST APIs, I would love to contribute to your engineering efforts.\n\nBest regards,\nNitin Chander\n+91-8130489303 | nitinchandra834@gmail.com`,
        status: 'Not Applied',
        notes: ''
      };

      jobs.unshift(newJob);
      saveCustomJob(newJob);
      addJobForm.reset();
      addCompanyModal.classList.remove('show');
      updateStats();
      render();
      showToast(`🎉 Added "${comp}" to your job hunt tracker!`, 'success');
    });

    // Live Refresh Feed Button
    const btnRefreshJobs = document.getElementById('btnRefreshJobs');
    if (btnRefreshJobs) {
      btnRefreshJobs.addEventListener('click', async () => {
        btnRefreshJobs.classList.add('spinning');
        try {
          await syncLiveFeed(true);
        } finally {
          setTimeout(() => {
            btnRefreshJobs.classList.remove('spinning');
          }, 400);
        }
      });
    }

    // Role Slicer Pills
    if (roleSlicerPills) {
      roleSlicerPills.addEventListener('click', (e) => {
        const pill = e.target.closest('.role-pill');
        if (pill) {
          roleSlicerPills.querySelectorAll('.role-pill').forEach(b => b.classList.remove('active'));
          pill.classList.add('active');
          filters.roleCategory = pill.getAttribute('data-role');
          render();
        }
      });
    }

    // Resume Upload Triggers
    if (btnHeaderUploadResume && resumeFileInput) {
      btnHeaderUploadResume.addEventListener('click', () => resumeFileInput.click());
    }
    if (btnHubUploadResume && resumeFileInput) {
      btnHubUploadResume.addEventListener('click', () => resumeFileInput.click());
    }
    if (btnChangeResume && resumeFileInput) {
      btnChangeResume.addEventListener('click', () => resumeFileInput.click());
    }
    if (resumeFileInput) {
      resumeFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          handleResumeUpload(e.target.files[0]);
        }
      });
    }
    if (btnLoadDefaultResume) {
      btnLoadDefaultResume.addEventListener('click', loadDefaultResume);
    }
    if (btnResetResumeOrder) {
      btnResetResumeOrder.addEventListener('click', resetResumeRanking);
    }
  }

  // --- Resume Matching & Scoring Logic ---
  const CLIENT_SKILL_PATTERNS = {
    'Generative AI': /\b(generative ai|genai|gen ai)\b/i,
    'LLMs': /\b(llm|llms|large language model)\b/i,
    'RAG': /\b(rag|retrieval[- ]augmented)\b/i,
    'LangChain': /\blangchain\b/i,
    'LangGraph': /\blanggraph\b/i,
    'Prompt Engineering': /\bprompt engineering\b/i,
    'Transformers': /\b(transformers?|hugging\s*face)\b/i,
    'NLP': /\b(nlp|natural language processing)\b/i,
    'ChromaDB': /\bchroma(db)?\b/i,
    'FAISS': /\bfaiss\b/i,
    'Computer Vision': /\b(computer vision|opencv)\b/i,
    'Python': /\bpython\b/i,
    'Machine Learning': /\b(machine learning|ml)\b/i,
    'Deep Learning': /\b(deep learning|dl)\b/i,
    'Scikit-learn': /\b(scikit[- ]learn|sklearn)\b/i,
    'PyTorch': /\bpytorch\b/i,
    'TensorFlow': /\b(tensorflow|keras)\b/i,
    'Pandas': /\bpandas\b/i,
    'NumPy': /\bnumpy\b/i,
    'XGBoost': /\bxgboost\b/i,
    'Data Science': /\bdata scien(ce|tist)\b/i,
    'SQL': /\b(sql|postgresql|mysql)\b/i,
    'Data Engineering': /\b(data engineering|data engineer|etl)\b/i,
    'FastAPI': /\bfastapi\b/i,
    'Flask': /\bflask\b/i,
    'REST APIs': /\b(rest|restful|apis?)\b/i,
    'Docker': /\bdocker\b/i,
    'AWS': /\b(aws|amazon web services|ec2|s3)\b/i,
    'MLflow': /\b(mlflow|mlops)\b/i
  };

  async function handleResumeUpload(file) {
    showToast(`📄 Uploading and analyzing ${file.name}...`, 'info');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/resume/upload', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server returned ${res.status}`);
      }
      const data = await res.json();
      applyResumeScoring(data);
    } catch (err) {
      console.warn('Backend upload failed or offline, analyzing locally:', err);
      readAndScoreLocally(file);
    }
  }

  async function loadDefaultResume() {
    showToast('⚡ Analyzing against Nitin_resume.pdf...', 'info');
    try {
      const res = await fetch('/api/resume/default');
      if (!res.ok) throw new Error('Default resume endpoint failed');
      const data = await res.json();
      applyResumeScoring(data);
    } catch (err) {
      showToast('⚠️ Could not load default resume from server.', 'error');
    }
  }

  function readAndScoreLocally(file) {
    const reader = new FileReader();
    reader.onload = function(evt) {
      const text = evt.target.result || '';
      const extractedSkills = [];
      Object.entries(CLIENT_SKILL_PATTERNS).forEach(([skill, regex]) => {
        if (regex.test(text)) extractedSkills.push(skill);
      });
      if (extractedSkills.length === 0) {
        extractedSkills.push('Python', 'SQL', 'FastAPI', 'Machine Learning', 'RAG');
      }

      const scoredJobs = jobs.map(j => {
        const scoreData = scoreJobClientSide(j, extractedSkills);
        return {
          id: j.id,
          fitScore: scoreData.fitScore,
          fitTier: scoreData.fitTier,
          matchedSkills: scoreData.matchedSkills,
          resumeMatchScore: scoreData.resumeMatchScore
        };
      });

      applyResumeScoring({
        status: 'success',
        filename: file.name,
        profile: {
          name: 'Uploaded Candidate',
          skills: extractedSkills
        },
        jobs: scoredJobs
      });
    };
    reader.readAsText(file);
  }

  function scoreJobClientSide(job, skills) {
    const skillsSet = new Set(skills);
    const combined = `${(job.title || '')} ${(job.description || '')} ${(job.matchRationale || '')}`.toLowerCase();
    
    // Title alignment (up to 40)
    let titleScore = 20;
    const t = (job.title || '').toLowerCase();
    if (t.includes('ai') || t.includes('genai') || t.includes('llm')) {
      titleScore = skillsSet.has('Generative AI') || skillsSet.has('LLMs') || skillsSet.has('RAG') ? 40 : 25;
    } else if (t.includes('machine learning') || t.includes('ml')) {
      titleScore = skillsSet.has('Machine Learning') || skillsSet.has('Scikit-learn') ? 40 : 25;
    } else if (t.includes('data scientist') || t.includes('data science')) {
      titleScore = skillsSet.has('Data Science') || skillsSet.has('Python') ? 38 : 24;
    } else if (t.includes('data engineer') || t.includes('etl') || t.includes('spark')) {
      titleScore = skillsSet.has('SQL') || skillsSet.has('Data Engineering') ? 38 : 22;
    } else if (t.includes('python') || t.includes('backend') || t.includes('developer')) {
      titleScore = skillsSet.has('Python') || skillsSet.has('FastAPI') ? 36 : 22;
    }

    // Skills overlap (up to 40)
    const matched = [];
    skills.forEach(s => {
      const pat = CLIENT_SKILL_PATTERNS[s];
      if (pat && pat.test(combined)) {
        matched.push(s);
      }
    });
    const overlapRatio = Math.min(1.0, matched.length / 4.0);
    const skillScore = Math.floor(overlapRatio * 40);

    // Experience (up to 12)
    const expScore = (t.includes('intern') || t.includes('entry') || t.includes('fresher') || t.includes('junior')) ? 12 : 8;
    const locScore = 8;
    const total = Math.max(48, Math.min(98, titleScore + skillScore + expScore + locScore));
    const tier = total >= 75 ? 'High' : (total >= 60 ? 'Medium' : 'Stretch');

    return {
      fitScore: total,
      fitTier: tier,
      matchedSkills: matched.slice(0, 5),
      resumeMatchScore: total
    };
  }

  function applyResumeScoring(data) {
    if (!data || !data.jobs) return;
    
    // Create lookup of scored jobs
    const scoreMap = new Map();
    data.jobs.forEach(j => {
      scoreMap.set(j.id, {
        fitScore: j.resumeMatchScore || j.fitScore,
        fitTier: j.fitTier,
        matchedSkills: j.matchedSkills || [],
        resumeMatchScore: j.resumeMatchScore || j.fitScore
      });
    });

    // Update current jobs array
    jobs.forEach(j => {
      if (scoreMap.has(j.id)) {
        const s = scoreMap.get(j.id);
        j.fitScore = s.fitScore;
        j.fitTier = s.fitTier;
        j.matchedSkills = s.matchedSkills;
        j.resumeMatchScore = s.resumeMatchScore;
      }
    });

    // Update UI active state
    if (resumeHubInactive && resumeHubActive) {
      resumeHubInactive.style.display = 'none';
      resumeHubActive.style.display = 'block';
    }
    if (activeResumeName) {
      activeResumeName.textContent = data.filename || 'Resume';
    }
    if (activeResumeMeta) {
      const skillsCount = (data.profile && data.profile.skills) ? data.profile.skills.length : 25;
      const topScore = data.jobs.length > 0 ? (data.jobs[0].resumeMatchScore || 98) : 95;
      activeResumeMeta.textContent = `• ${skillsCount} skills detected • Top Match: ${topScore}%`;
    }
    if (activeResumeSkillsList && data.profile && data.profile.skills) {
      activeResumeSkillsList.innerHTML = data.profile.skills.map(s => `<span class="skill-chip highlight">${escapeHtml(s)}</span>`).join('');
    }

    // Automatically set sort to Highest Fit First
    filters.sort = 'fit-desc';
    if (sortSelect) sortSelect.value = 'fit-desc';

    updateStats();
    render();
    showToast(`🎯 Opportunities ranked! Showing highest fit roles for ${data.filename || 'your resume'} first.`, 'success');
  }

  function resetResumeRanking() {
    if (resumeHubInactive && resumeHubActive) {
      resumeHubActive.style.display = 'none';
      resumeHubInactive.style.display = 'flex';
    }
    filters.sort = 'date-desc';
    if (sortSelect) sortSelect.value = 'date-desc';
    render();
    showToast('Reset order to Date Posted (Newest First).', 'info');
  }

  // 9. Modal Open Helper
  function openDetailModal(jobId) {
    const job = jobs.find(j => j.id === jobId);
    if (!job) return;

    activeModalJob = job;

    modalCompanyName.textContent = job.company;
    modalRoleTitle.textContent = `${job.title} • ${job.location}`;
    modalFitScore.textContent = `${job.fitScore}% Fit`;
    modalFitTier.textContent = `${job.fitTier} Probability Role`;
    modalSalary.textContent = job.salary || 'Competitive';
    modalSource.textContent = `Platform: ${job.source || 'Direct'}`;
    const modalPostedDate = document.getElementById('modalPostedDate');
    if (modalPostedDate) {
      modalPostedDate.textContent = `Posted: ${formatDate(job.postedDate, job.id)}`;
    }
    modalRationale.textContent = job.matchRationale || 'Strong alignment based on technical skills and profile requirements.';

    if (job.link) {
      modalApplyLink.href = job.link;
      modalApplyLink.style.display = 'inline-flex';
    } else {
      modalApplyLink.style.display = 'none';
    }

    modalEmailAngle.textContent = job.coldEmailAngle || 'Personalized technical outreach showcasing Python and GenAI capabilities.';
    modalEmailSubject.textContent = job.coldEmailSubject || `Application for ${job.title} | Nitin Chander`;
    modalEmailBody.textContent = job.coldEmailBody || 'Email draft not generated.';

    // Populate Overview Tab Recruiter Card
    if (modalOverviewContactCard) {
      const hasEmail = job.contactEmail && isValidEmail(job.contactEmail);
      modalOverviewContactCard.style.display = 'block';
      if (modalOverviewContactName) {
        modalOverviewContactName.textContent = job.contactName || (job.company + ' Hiring Team');
      }
      if (modalOverviewEmail) {
        if (hasEmail) {
          modalOverviewEmail.href = `mailto:${job.contactEmail.trim()}`;
          modalOverviewEmail.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg> <span>${escapeHtml(job.contactEmail)}</span>`;
          modalOverviewEmail.style.display = 'inline-flex';
          modalOverviewEmail.title = `Send email to ${job.contactEmail}${job.emailVerified ? ' (Verified)' : ' (Unverified)'}`;
        } else {
          modalOverviewEmail.style.display = 'none';
        }
      }

      // Company LinkedIn button in Overview Tab
      if (modalOverviewCompanyLinkedIn) {
        const companyUrl = getCompanyLinkedInUrl(job);
        const isCompanyVerified = Boolean(job.companyLinkedIn && job.companyLinkedInVerified && isValidUrl(job.companyLinkedIn));
        modalOverviewCompanyLinkedIn.href = companyUrl;
        modalOverviewCompanyLinkedIn.target = '_blank';
        modalOverviewCompanyLinkedIn.rel = 'noopener noreferrer';
        modalOverviewCompanyLinkedIn.style.display = 'inline-flex';
        modalOverviewCompanyLinkedIn.className = isCompanyVerified ? 'contact-badge contact-company-badge' : 'contact-badge contact-company-search-badge';
        modalOverviewCompanyLinkedIn.innerHTML = isCompanyVerified
          ? `<svg width="11" height="11" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v7.6h2.8v-7.6h-2.8M7.86 6.54a1.63 1.63 0 1 0 0 3.26 1.63 1.63 0 0 0 0-3.26z"/></svg> <span>Company LinkedIn</span>`
          : `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> <span>Find Company on LinkedIn</span>`;
        modalOverviewCompanyLinkedIn.title = isCompanyVerified ? `Company LinkedIn: ${job.company}` : `Find ${job.company} on LinkedIn`;
        modalOverviewCompanyLinkedIn.onclick = (e) => e.stopPropagation();
      }

      // Recruiter LinkedIn button in Overview Tab
      if (modalOverviewRecruiterLinkedIn) {
        const recruiterUrl = getRecruiterLinkedInUrl(job);
        const isRecruiterVerified = Boolean(job.recruiterLinkedIn && job.recruiterLinkedInVerified && isValidUrl(job.recruiterLinkedIn));
        modalOverviewRecruiterLinkedIn.href = recruiterUrl;
        modalOverviewRecruiterLinkedIn.target = '_blank';
        modalOverviewRecruiterLinkedIn.rel = 'noopener noreferrer';
        modalOverviewRecruiterLinkedIn.style.display = 'inline-flex';
        modalOverviewRecruiterLinkedIn.className = isRecruiterVerified ? 'contact-badge contact-recruiter-badge' : 'contact-badge contact-recruiter-search-badge';
        modalOverviewRecruiterLinkedIn.innerHTML = isRecruiterVerified
          ? `<svg width="11" height="11" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v7.6h2.8v-7.6h-2.8M7.86 6.54a1.63 1.63 0 1 0 0 3.26 1.63 1.63 0 0 0 0-3.26z"/></svg> <span>Recruiter LinkedIn</span>`
          : `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> <span>Find Recruiter</span>`;
        modalOverviewRecruiterLinkedIn.title = isRecruiterVerified ? `Recruiter LinkedIn: ${job.contactName || job.company}` : `Search LinkedIn People for ${job.contactName || job.company}`;
        modalOverviewRecruiterLinkedIn.onclick = (e) => e.stopPropagation();
      }

      // Backward compatibility alias for modalOverviewLinkedIn
      if (modalOverviewLinkedIn) {
        modalOverviewLinkedIn.href = getCompanyLinkedInUrl(job);
      }
    }

    // Populate recruiter card in Cold Email Tab
    if (modalRecruiterName) modalRecruiterName.textContent = job.contactName || (job.company + ' Hiring Team');
    if (modalContactEmail) {
      const email = (job.contactEmail || '').trim();
      if (email && isValidEmail(email)) {
        modalContactEmail.textContent = '✉ ' + email + (job.emailVerified ? ' (Verified)' : '');
        modalContactEmail.href = 'mailto:' + email;
        modalContactEmail.title = 'Click to send email to ' + email + (job.emailVerified ? ' (Verified)' : ' (Unverified)');
        modalContactEmail.style.cursor = 'pointer';
        modalContactEmail.style.opacity = '1';
        modalContactEmail.style.pointerEvents = 'auto';
        modalContactEmail.onclick = (e) => e.stopPropagation();
      } else {
        modalContactEmail.textContent = email ? ('✉ ' + email) : 'No email available';
        modalContactEmail.removeAttribute('href');
        modalContactEmail.title = 'Email unavailable or invalid';
        modalContactEmail.style.cursor = 'default';
        modalContactEmail.style.opacity = '0.5';
        modalContactEmail.style.pointerEvents = 'none';
        modalContactEmail.onclick = (e) => e.preventDefault();
      }
    }

    // Company LinkedIn button in Cold Email Tab
    if (modalCompanyLinkedIn) {
      const companyUrl = getCompanyLinkedInUrl(job);
      const isCompanyVerified = Boolean(job.companyLinkedIn && job.companyLinkedInVerified && isValidUrl(job.companyLinkedIn));
      modalCompanyLinkedIn.href = companyUrl;
      modalCompanyLinkedIn.target = '_blank';
      modalCompanyLinkedIn.rel = 'noopener noreferrer';
      modalCompanyLinkedIn.style.display = 'inline-flex';
      modalCompanyLinkedIn.title = isCompanyVerified ? `Company LinkedIn: ${job.company}` : `Find ${job.company} on LinkedIn`;
      modalCompanyLinkedIn.innerHTML = isCompanyVerified
        ? `<span>Company LinkedIn</span> <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>`
        : `<span>Find Company on LinkedIn</span> <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
      modalCompanyLinkedIn.onclick = (e) => e.stopPropagation();
    }

    // Recruiter LinkedIn button in Cold Email Tab
    if (modalRecruiterLinkedIn) {
      const recruiterUrl = getRecruiterLinkedInUrl(job);
      const isRecruiterVerified = Boolean(job.recruiterLinkedIn && job.recruiterLinkedInVerified && isValidUrl(job.recruiterLinkedIn));
      modalRecruiterLinkedIn.href = recruiterUrl;
      modalRecruiterLinkedIn.target = '_blank';
      modalRecruiterLinkedIn.rel = 'noopener noreferrer';
      modalRecruiterLinkedIn.style.display = 'inline-flex';
      modalRecruiterLinkedIn.style.opacity = '1';
      modalRecruiterLinkedIn.style.cursor = 'pointer';
      modalRecruiterLinkedIn.style.pointerEvents = 'auto';
      modalRecruiterLinkedIn.onclick = (e) => e.stopPropagation();

      if (isRecruiterVerified) {
        modalRecruiterLinkedIn.title = `Open verified Recruiter LinkedIn profile in new tab`;
        modalRecruiterLinkedIn.innerHTML = `<span>Recruiter LinkedIn</span> <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>`;
      } else {
        modalRecruiterLinkedIn.title = `Search LinkedIn People for ${job.contactName || job.company}`;
        modalRecruiterLinkedIn.innerHTML = `<span>Find Recruiter</span> <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
      }
    }
    if (btnCopyContactEmail) {
      btnCopyContactEmail.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (job.contactEmail && isValidEmail(job.contactEmail)) {
          navigator.clipboard.writeText(job.contactEmail.trim()).then(() => {
            showToast(`Copied ${job.contactEmail.trim()} to clipboard!`, 'success');
          }).catch(() => {
            showToast(`Contact email: ${job.contactEmail.trim()}`, 'info');
          });
        } else {
          showToast('No contact email available to copy.', 'warning');
        }
      };
    }

    // Setup mailto link with pre-filled To: email address
    const toEmail = job.contactEmail ? encodeURIComponent(job.contactEmail) : '';
    const mailSubject = encodeURIComponent(job.coldEmailSubject || `Application for ${job.title} | Nitin Chander`);
    const mailBody = encodeURIComponent(job.coldEmailBody || '');
    btnMailto.href = `mailto:${toEmail}?subject=${mailSubject}&body=${mailBody}`;

    modalFullDesc.textContent = job.description || 'No detailed description available.';
    modalStatusSelect.value = job.status || 'Not Applied';
    modalNotesText.value = job.notes || '';

    // Reset to overview tab
    document.querySelector('.modal-tab-btn[data-tab="overview"]').click();

    detailModal.classList.add('show');
  }

  function copyJobEmail(job) {
    const textToCopy = `Subject: ${job.coldEmailSubject || ''}\n\n${job.coldEmailBody || ''}`;
    navigator.clipboard.writeText(textToCopy).then(() => {
      showToast(`✉️ Copied cold email for "${job.company}" to clipboard!`, 'success');
    }).catch(() => {
      showToast('Could not access clipboard automatically.', 'warning');
    });
  }

  // 10. Utilities
  function formatDate(dateStr, jobId) {
    let raw = dateStr;
    if (!raw && jobId && EXACT_JOB_DATES[jobId]) {
      raw = EXACT_JOB_DATES[jobId];
    }
    if (!raw || typeof raw !== 'string') {
      raw = '2026-10-24 09:30:00';
    }
    const trimmed = raw.trim();
    try {
      const parts = trimmed.split(/[\sT]+/);
      const dateParts = parts[0].split('-');
      if (dateParts.length === 3) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const year = dateParts[0];
        const monthIdx = parseInt(dateParts[1], 10) - 1;
        const day = parseInt(dateParts[2], 10);
        if (monthIdx >= 0 && monthIdx < 12 && !isNaN(day)) {
          let dateFormatted = `${months[monthIdx]} ${day}, ${year}`;
          if (parts[1]) {
            const timeParts = parts[1].split(':');
            if (timeParts.length >= 2) {
              let hour = parseInt(timeParts[0], 10);
              const minute = timeParts[1].padStart(2, '0');
              const ampm = hour >= 12 ? 'PM' : 'AM';
              hour = hour % 12;
              hour = hour ? hour : 12;
              return `${dateFormatted}, ${hour}:${minute} ${ampm}`;
            }
          }
          return dateFormatted;
        }
      }
      return trimmed;
    } catch {
      return trimmed;
    }
  }

  function getLocalTimestampString(d = new Date()) {
    const pad = (n) => String(n).padStart(2, '0');
    const yyyy = d.getFullYear();
    const mm = pad(d.getMonth() + 1);
    const dd = pad(d.getDate());
    const hh = pad(d.getHours());
    const min = pad(d.getMinutes());
    const ss = pad(d.getSeconds());
    return `${yyyy}-${mm}-${dd} ${hh}:${min}:${ss}`;
  }

  function isValidEmail(email) {
    if (!email || typeof email !== 'string') return false;
    const trimmed = email.trim();
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(trimmed);
  }

  function isValidUrl(url) {
    if (!url || typeof url !== 'string') return false;
    const trimmed = url.trim();
    try {
      const u = new URL(trimmed);
      return u.protocol === 'http:' || u.protocol === 'https:';
    } catch {
      return false;
    }
  }

  function getCompanyLinkedInUrl(job) {
    if (job && job.companyLinkedIn && job.companyLinkedInVerified && isValidUrl(job.companyLinkedIn)) {
      return job.companyLinkedIn.trim();
    }
    const cleanComp = (job && job.company) ? job.company.replace(/\b(Inc|Pvt\.?|Ltd\.?|Private|Limited|Technologies|LLC)\b/gi, '').trim() : 'Company';
    return `https://www.linkedin.com/search/results/companies/?keywords=${encodeURIComponent(cleanComp || job.company)}`;
  }

  function getRecruiterLinkedInUrl(job) {
    if (job && job.recruiterLinkedIn && job.recruiterLinkedInVerified && isValidUrl(job.recruiterLinkedIn)) {
      return job.recruiterLinkedIn.trim();
    }
    if (!job) return 'https://www.linkedin.com/search/results/people/?keywords=Recruiter';
    const parts = [];
    if (job.contactName) {
      let cleanName = job.contactName.replace(/\s*\([^)]*\)/g, '').trim();
      cleanName = cleanName.replace(/\s+N\.S\./g, '').trim();
      parts.push(cleanName);
    }
    if (job.company) {
      const cleanComp = job.company.replace(/\b(Inc|Pvt\.?|Ltd\.?|Private|Limited|Technologies|LLC)\b/gi, '').trim();
      const compLower = (cleanComp || job.company).toLowerCase();
      const nameLower = (job.contactName || '').toLowerCase();
      if (!nameLower.includes(compLower)) {
        parts.push(cleanComp || job.company);
      }
    }
    const query = parts.join(' ').trim() || (job.company ? `${job.company} Recruiter` : 'Recruiter');
    return `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(query)}`;
  }

  function getLinkedInSearchUrl(job) {
    return getRecruiterLinkedInUrl(job);
  }

  function getStatusClass(status) {
    switch (status) {
      case 'Applied': return 'applied';
      case 'Cold Emailed': return 'emailed';
      case 'Interviewing': return 'interviewing';
      case 'Offer': return 'offer';
      default: return '';
    }
  }

  function isRecentlyPosted(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') return false;
    // Highlight roles posted in the last 48 hours (Oct 28–29, 2026)
    return dateStr.startsWith('2026-10-29') || dateStr.startsWith('2026-10-28');
  }

  function getSourceClass(src) {
    if (!src) return 'direct';
    const s = src.toLowerCase();
    if (s.includes('linkedin')) return 'linkedin';
    if (s.includes('naukri')) return 'naukri';
    if (s.includes('indeed')) return 'indeed';
    return 'direct';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') toast.style.borderLeftColor = 'var(--accent-rose)';
    if (type === 'warning') toast.style.borderLeftColor = 'var(--accent-amber)';

    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Start App
  document.addEventListener('DOMContentLoaded', () => {
    initData();
    setupEventListeners();

    // Periodic time-to-time auto-sync (every 15 minutes when dashboard is active)
    setInterval(() => {
      syncLiveFeed(false);
    }, 15 * 60 * 1000);
  });

})();
