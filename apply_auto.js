/**
 * apply_auto.js
 * Auto-Apply feature module for Job Hunt Intelligence dashboard.
 * 
 * DESIGN RULES:
 *  - Does NOT modify app.js or any existing code.
 *  - Reads job data from window.INITIAL_JOBS_DATA (already set by jobs_data.js).
 *  - Communicates with the FastAPI backend at /api/*
 *  - Updates job status in localStorage only after confirmed submission.
 *  - All UI elements are injected via this file only.
 */

(function () {
  'use strict';

  const API_BASE = '';  // Same origin — FastAPI serves both static files and /api/
  const STORAGE_KEY = 'job_hunt_tracker_store_v1';  // Same key as app.js
  const POLL_INTERVAL_MS = 2000;

  // Active polling interval handle
  let _pollHandle = null;
  let _activeSessionId = null;
  let _activeJobId = null;

  // ── Status display labels ──────────────────────────────────────────────── //
  const STATUS_ICONS = {
    'Pending':                    { icon: '⏳', cls: 'status-pending' },
    'Opening application':        { icon: '🌐', cls: 'status-opening' },
    'Detecting form':             { icon: '🔍', cls: 'status-detecting' },
    'Filling details':            { icon: '✍️', cls: 'status-filling' },
    'Resume uploaded':            { icon: '📎', cls: 'status-uploading' },
    'Waiting for review':         { icon: '✋', cls: 'status-waiting' },
    'Submitted successfully':     { icon: '✅', cls: 'status-submitted' },
    'Needs manual action':        { icon: '⚠️', cls: 'status-manual' },
    'Failed':                     { icon: '❌', cls: 'status-failed' },
    'Aborted by user':            { icon: '🛑', cls: 'status-aborted' },
    'Duplicate — already applied':{ icon: '🔁', cls: 'status-duplicate' },
    'Ready':                      { icon: '🟢', cls: 'status-ready' },
  };

  // ── Inject progress panel HTML into the page ───────────────────────────── //
  function injectProgressPanel() {
    if (document.getElementById('autoApplyPanel')) return;

    const panel = document.createElement('div');
    panel.id = 'autoApplyPanel';
    panel.className = 'auto-apply-panel';
    panel.style.display = 'none';
    panel.innerHTML = `
      <div class="aap-header">
        <div class="aap-title">
          <span class="aap-icon">⚡</span>
          <strong>Auto-Apply Progress</strong>
          <span id="aapCompanyLabel" class="aap-company-label"></span>
        </div>
        <button id="aapCloseBtn" class="aap-close-btn" title="Close panel">✕</button>
      </div>
      <div class="aap-body">
        <div class="aap-status-row">
          <span id="aapStatusIcon" class="aap-status-icon">⏳</span>
          <span id="aapStatusText" class="aap-status-text">Ready</span>
        </div>
        <div id="aapProgressBar" class="aap-progress-bar">
          <div id="aapProgressFill" class="aap-progress-fill" style="width:0%"></div>
        </div>
        <div id="aapMessage" class="aap-message"></div>
        <div id="aapError" class="aap-error" style="display:none;"></div>
        <div id="aapConfirmSection" class="aap-confirm-section" style="display:none;">
          <div class="aap-confirm-notice">
            📋 <strong>Review the filled application</strong> in the browser window that opened.
            Check every field carefully, then confirm or abort below.
          </div>
          <div class="aap-confirm-buttons">
            <button id="aapConfirmBtn" class="aap-btn-confirm">
              ✅ Confirm &amp; Submit Application
            </button>
            <button id="aapAbortBtn" class="aap-btn-abort">
              🛑 Abort — Don't Submit
            </button>
          </div>
        </div>
        <div id="aapSuccessSection" class="aap-success-section" style="display:none;">
          <div class="aap-success-msg">
            🎉 Application submitted! Status updated to <strong>Applied</strong>.
          </div>
          <button id="aapViewHistoryBtn" class="aap-btn-secondary">View Application History</button>
        </div>
        <div id="aapRetrySection" class="aap-retry-section" style="display:none;">
          <button id="aapRetryBtn" class="aap-btn-abort" style="background: rgba(245,158,11,0.15); border-color: rgba(245,158,11,0.4); color: #f59e0b;">
            🔁 Retry Application
          </button>
        </div>
      </div>
    `;

    // Insert before closing </main> or append to body
    const main = document.querySelector('main.main-container');
    if (main) {
      main.appendChild(panel);
    } else {
      document.body.appendChild(panel);
    }

    // Bind panel buttons
    document.getElementById('aapCloseBtn').addEventListener('click', hidePanel);
    document.getElementById('aapConfirmBtn').addEventListener('click', confirmSubmission);
    document.getElementById('aapAbortBtn').addEventListener('click', abortApplication);
    document.getElementById('aapViewHistoryBtn').addEventListener('click', showHistoryModal);
    document.getElementById('aapRetryBtn').addEventListener('click', () => {
      if (_activeJobId) retryApplication(_activeJobId);
    });
  }

  // ── Inject the Apply Automatically button into table rows & modal ──────── //
  function injectApplyButtons() {
    // Use event delegation on the document for table rows (they're re-rendered)
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-auto-apply');
      if (btn) {
        e.preventDefault();
        e.stopPropagation();
        const jobId = btn.getAttribute('data-id');
        startAutoApply(jobId);
      }
    });
  }

  // Patch the job card / table row rendering to include the auto-apply button.
  // We hook into the MutationObserver on the jobs table body.
  function observeJobsTable() {
    const tableBody = document.getElementById('jobsTableBody');
    const cardsView = document.getElementById('cardsViewSection');

    const observer = new MutationObserver(() => {
      addApplyButtonsToRows();
    });

    if (tableBody) observer.observe(tableBody, { childList: true });
    if (cardsView) observer.observe(cardsView, { childList: true });
  }

  function addApplyButtonsToRows() {
    // Table rows — add button to action column if not already added
    document.querySelectorAll('#jobsTableBody tr').forEach(row => {
      if (row.querySelector('.btn-auto-apply')) return; // Already added

      const actionCell = row.querySelector('.col-actions .action-group');
      if (!actionCell) return;

      const jobId = row.querySelector('[data-id]')?.getAttribute('data-id');
      if (!jobId) return;

      const btn = document.createElement('button');
      btn.className = 'btn-icon btn-auto-apply';
      btn.setAttribute('data-id', jobId);
      btn.setAttribute('title', 'Apply Automatically');
      btn.innerHTML = `
        <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>`;
      actionCell.appendChild(btn);
    });

    // Card view
    document.querySelectorAll('#cardsViewSection .job-card').forEach(card => {
      if (card.querySelector('.btn-auto-apply')) return;

      const actionGroup = card.querySelector('.action-group');
      if (!actionGroup) return;

      const jobId = card.querySelector('[data-id]')?.getAttribute('data-id');
      if (!jobId) return;

      const btn = document.createElement('button');
      btn.className = 'btn-icon btn-auto-apply';
      btn.setAttribute('data-id', jobId);
      btn.setAttribute('title', 'Apply Automatically');
      btn.innerHTML = `
        <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>`;
      actionGroup.appendChild(btn);
    });
  }

  // ── Also inject into the detail modal ─────────────────────────────────── //
  function injectModalApplyButton() {
    const overviewPane = document.getElementById('tabOverview');
    if (!overviewPane) return;

    // Add an Apply Automatically button below the existing Open Link button
    if (document.getElementById('modalAutoApplyBtn')) return;

    const btn = document.createElement('button');
    btn.id = 'modalAutoApplyBtn';
    btn.className = 'btn-auto-apply-modal';
    btn.innerHTML = `
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M13 10V3L4 14h7v7l9-11h-7z"/>
      </svg>
      Apply Automatically`;

    btn.addEventListener('click', () => {
      // Get the active job ID from the modal (app.js stores it in activeModalJob)
      // We read it by checking which modal is visible and looking at title
      const companyEl = document.getElementById('modalCompanyName');
      if (!companyEl) return;
      const company = companyEl.textContent.trim();

      // Find job by company name from global data
      const allJobs = window.INITIAL_JOBS_DATA || [];
      // Also check locally-added jobs in storage
      let job = allJobs.find(j => j.company === company);
      if (!job) {
        // Try from storage
        try {
          const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
          const custom = stored.__custom_jobs || [];
          job = custom.find(j => j.company === company);
        } catch {}
      }

      if (job) {
        startAutoApply(String(job.id));
      } else {
        showToastMsg('Could not identify the job. Please use the ⚡ button in the table row.', 'warning');
      }
    });

    // Insert into the overview action buttons div
    const actionDiv = overviewPane.querySelector('div[style*="gap: 12px"]');
    if (actionDiv) {
      actionDiv.appendChild(btn);
    }
  }

  // ── Core Application Flow ─────────────────────────────────────────────── //
  function findJobById(id) {
    const allJobs = window.INITIAL_JOBS_DATA || [];
    let job = allJobs.find(j => String(j.id) === String(id));
    if (!job) {
      try {
        const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        const custom = stored.__custom_jobs || [];
        job = custom.find(j => String(j.id) === String(id));
      } catch {}
    }
    return job;
  }

  async function startAutoApply(jobId) {
    const job = findJobById(jobId);
    if (!job) {
      showToastMsg('Job not found in dataset.', 'error');
      return;
    }

    if (!job.link) {
      showToastMsg(`No application link found for "${job.company}".`, 'warning');
      return;
    }

    // Check server is available
    const healthy = await checkServerHealth();
    if (!healthy) {
      showToastMsg(
        '❌ Auto-Apply server is not running. Start it with: python auto_apply_server.py',
        'error'
      );
      return;
    }

    showPanel(job.company, job.title);
    _activeJobId = jobId;

    // POST to /api/apply
    try {
      const res = await fetch(`${API_BASE}/api/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: String(job.id),
          company: job.company,
          role: job.title,
          apply_url: job.link,
          force: false
        })
      });

      const data = await res.json();

      if (data.status === 'duplicate') {
        updatePanelStatus('Duplicate — already applied', data.message);
        showRetryOption();
        return;
      }

      if (!data.session_id) {
        updatePanelStatus('Failed', data.message || data.detail || 'Unknown error');
        showRetryOption();
        return;
      }

      _activeSessionId = data.session_id;
      startPolling(_activeSessionId, job);

    } catch (err) {
      updatePanelStatus('Failed', `Could not start application: ${err.message}`);
      showRetryOption();
    }
  }

  function startPolling(sessionId, job) {
    clearPolling();
    _pollHandle = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/apply/${sessionId}/status`);
        if (!res.ok) { clearPolling(); return; }
        const data = await res.json();
        handleStatusUpdate(data, job);
      } catch (e) {
        console.warn('[auto-apply] Poll error:', e);
      }
    }, POLL_INTERVAL_MS);
  }

  function handleStatusUpdate(data, job) {
    const status = data.status;
    const message = data.progress_message || status;
    const error = data.error;

    updatePanelStatus(status, message, error);

    if (status === 'Waiting for review') {
      showConfirmSection();
    } else {
      hideConfirmSection();
    }

    if (status === 'Submitted successfully') {
      clearPolling();
      // Update job status in localStorage
      markJobApplied(job.id);
      showSuccessSection();
    }

    if (status === 'Failed' || status === 'Aborted by user') {
      clearPolling();
      showRetryOption();
    }

    if (status === 'Needs manual action') {
      // Don't clear polling — keep monitoring for user confirm/abort
    }
  }

  async function confirmSubmission() {
    if (!_activeSessionId) return;
    try {
      await fetch(`${API_BASE}/api/apply/${_activeSessionId}/confirm`, { method: 'POST' });
      hideConfirmSection();
      updatePanelStatus('Waiting for review', 'Confirmation sent — submitting…');
    } catch (e) {
      showToastMsg('Could not send confirmation. Is the server still running?', 'error');
    }
  }

  async function abortApplication() {
    if (!_activeSessionId) return;
    clearPolling();
    try {
      await fetch(`${API_BASE}/api/apply/${_activeSessionId}/abort`, { method: 'POST' });
    } catch {}
    updatePanelStatus('Aborted by user', 'Application aborted. No submission was made.');
    hideConfirmSection();
    showRetryOption();
  }

  function retryApplication(jobId) {
    _activeSessionId = null;
    clearRetryOption();
    hideSuccessSection();
    startAutoApply(jobId);
  }

  // ── Status Persistence ────────────────────────────────────────────────── //
  function markJobApplied(jobId) {
    try {
      let store = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      store[jobId] = { ...(store[jobId] || {}), status: 'Applied' };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store));

      // Also update in-memory INITIAL_JOBS_DATA if available
      if (window.INITIAL_JOBS_DATA) {
        const job = window.INITIAL_JOBS_DATA.find(j => String(j.id) === String(jobId));
        if (job) job.status = 'Applied';
      }

      showToastMsg(`✅ Status updated to "Applied" for job #${jobId}`, 'success');
    } catch (e) {
      console.warn('[auto-apply] Could not update status in localStorage:', e);
    }
  }

  // ── Panel UI Helpers ──────────────────────────────────────────────────── //
  const PROGRESS_MAP = {
    'Pending':                    5,
    'Opening application':       20,
    'Detecting form':            35,
    'Filling details':           55,
    'Resume uploaded':           70,
    'Waiting for review':        85,
    'Submitted successfully':   100,
    'Needs manual action':       80,
    'Failed':                    0,
    'Aborted by user':           0,
  };

  function showPanel(company, role) {
    const panel = document.getElementById('autoApplyPanel');
    if (!panel) return;
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    const label = document.getElementById('aapCompanyLabel');
    if (label) label.textContent = `— ${company} · ${role}`;

    document.getElementById('aapError').style.display = 'none';
    hideConfirmSection();
    hideSuccessSection();
    clearRetryOption();
    updatePanelStatus('Pending', 'Starting automation…');
  }

  function hidePanel() {
    const panel = document.getElementById('autoApplyPanel');
    if (panel) panel.style.display = 'none';
    clearPolling();
  }

  function updatePanelStatus(status, message, error) {
    const info = STATUS_ICONS[status] || { icon: '⏳', cls: 'status-pending' };

    const iconEl = document.getElementById('aapStatusIcon');
    const textEl = document.getElementById('aapStatusText');
    const msgEl = document.getElementById('aapMessage');
    const fillEl = document.getElementById('aapProgressFill');
    const errEl = document.getElementById('aapError');

    if (iconEl) iconEl.textContent = info.icon;
    if (textEl) {
      textEl.textContent = status;
      textEl.className = `aap-status-text ${info.cls}`;
    }
    if (msgEl) msgEl.textContent = message || '';
    if (fillEl) fillEl.style.width = (PROGRESS_MAP[status] || 0) + '%';
    if (errEl) {
      if (error) {
        errEl.textContent = `Error: ${error}`;
        errEl.style.display = 'block';
      } else {
        errEl.style.display = 'none';
      }
    }
  }

  function showConfirmSection() {
    const el = document.getElementById('aapConfirmSection');
    if (el) el.style.display = 'block';
  }
  function hideConfirmSection() {
    const el = document.getElementById('aapConfirmSection');
    if (el) el.style.display = 'none';
  }
  function showSuccessSection() {
    const el = document.getElementById('aapSuccessSection');
    if (el) el.style.display = 'block';
  }
  function hideSuccessSection() {
    const el = document.getElementById('aapSuccessSection');
    if (el) el.style.display = 'none';
  }
  function showRetryOption() {
    const el = document.getElementById('aapRetrySection');
    if (el) el.style.display = 'block';
  }
  function clearRetryOption() {
    const el = document.getElementById('aapRetrySection');
    if (el) el.style.display = 'none';
  }
  function clearPolling() {
    if (_pollHandle) {
      clearInterval(_pollHandle);
      _pollHandle = null;
    }
  }

  // ── Application History Modal ─────────────────────────────────────────── //
  async function showHistoryModal() {
    try {
      const res = await fetch(`${API_BASE}/api/history`);
      const history = await res.json();

      let existing = document.getElementById('applyHistoryModal');
      if (existing) existing.remove();

      const modal = document.createElement('div');
      modal.id = 'applyHistoryModal';
      modal.className = 'modal-overlay show';
      modal.innerHTML = `
        <div class="modal-dialog" style="max-width:860px;">
          <div class="modal-header">
            <div class="modal-header-info">
              <h2>📋 Application History</h2>
              <p>${history.length} recorded attempt(s)</p>
            </div>
            <div style="display:flex;gap:10px;align-items:center;">
              <a href="/api/history/export" class="btn-excel" style="background:var(--gradient-excel);text-decoration:none;font-size:0.82rem;padding:7px 14px;">
                📥 Export Excel
              </a>
              <button class="btn-close" id="histModalClose">✕</button>
            </div>
          </div>
          <div class="modal-body" style="padding:0;">
            ${history.length === 0
              ? '<p style="padding:24px;color:var(--text-muted);">No applications recorded yet.</p>'
              : `<div style="overflow-x:auto;max-height:450px;">
                   <table class="jobs-table" style="min-width:720px;">
                     <thead>
                       <tr>
                         <th>Company</th><th>Role</th><th>Status</th>
                         <th>Attempted</th><th>Error</th>
                       </tr>
                     </thead>
                     <tbody>
                       ${history.map(r => `
                         <tr>
                           <td>${escapeHtml(r.company)}</td>
                           <td>${escapeHtml(r.role)}</td>
                           <td><span class="fit-badge ${r.status === 'Submitted successfully' ? 'fit-high' : (r.status === 'Failed' ? 'fit-stretch' : 'fit-medium')}">${escapeHtml(r.status)}</span></td>
                           <td style="font-family:var(--font-mono);font-size:0.78rem;">${(r.attempted_at || '').slice(0,16).replace('T',' ')}</td>
                           <td style="font-size:0.78rem;color:var(--accent-rose);">${escapeHtml(r.error_details || '')}</td>
                         </tr>`).join('')}
                     </tbody>
                   </table>
                 </div>`
            }
          </div>
        </div>`;

      document.body.appendChild(modal);
      modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
      document.getElementById('histModalClose').addEventListener('click', () => modal.remove());
    } catch (e) {
      showToastMsg('Could not load history. Is the server running?', 'error');
    }
  }

  // ── Server Health Check ───────────────────────────────────────────────── //
  async function checkServerHealth() {
    try {
      const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
      return res.ok;
    } catch {
      return false;
    }
  }

  // ── Utility ───────────────────────────────────────────────────────────── //
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function showToastMsg(message, type) {
    // Reuse app.js toast container if available
    const container = document.getElementById('toastContainer');
    if (!container) { console.warn(message); return; }
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') toast.style.borderLeftColor = '#f43f5e';
    if (type === 'warning') toast.style.borderLeftColor = '#f59e0b';
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ── Bootstrap ─────────────────────────────────────────────────────────── //
  function init() {
    injectProgressPanel();
    injectApplyButtons();
    observeJobsTable();

    // Inject modal button after modal first appears
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
      const mo = new MutationObserver(() => {
        if (detailModal.classList.contains('show')) {
          injectModalApplyButton();
        }
      });
      mo.observe(detailModal, { attributes: true, attributeFilter: ['class'] });
    }

    console.log('[auto-apply] Module initialised.');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();

