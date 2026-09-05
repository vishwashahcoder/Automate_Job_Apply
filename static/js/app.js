/* JobPulse AI - Multi-Platform Aggregator & Search Controller v3.0 */

let currentFilter = 'ALL';
let allJobsData = [];
let currentProfileData = {};

document.addEventListener('DOMContentLoaded', () => {
  loadProfile();
  loadStats();
  loadJobs();
  setupSSEStream();
  setupDragAndDrop();
});

// Load candidate profile into modal
async function loadProfile() {
  try {
    const res = await fetch('/api/profile');
    const data = await res.json();
    currentProfileData = data;
    populateProfileForm(data);
  } catch (err) {
    console.error('Error loading profile:', err);
  }
}

// Populate editable form inputs from candidate profile data
function populateProfileForm(configData) {
  const profile = configData.resume_profile || {};

  document.getElementById('profFullName').value = profile.full_name || '';
  document.getElementById('profEmail').value = profile.email || '';
  document.getElementById('profPhone').value = profile.phone || '';
  document.getElementById('profLinkedin').value = profile.linkedin_url || '';
  document.getElementById('profPortfolio').value = profile.portfolio_url || '';
  document.getElementById('profLocation').value = profile.location || '';
  document.getElementById('profLastPosition').value = profile.last_position || '';
  document.getElementById('profExp').value = profile.years_experience !== undefined ? profile.years_experience : '';
  document.getElementById('profSkills').value = (profile.skills || []).join(', ');
  document.getElementById('profSummary').value = profile.summary || '';

  // Default filter query if empty
  const filterQ = document.getElementById('filterQuery');
  if (filterQ && !filterQ.value && profile.last_position) {
    filterQ.value = profile.last_position;
  }

  // Show View Resume button if path exists
  if (profile.resume_pdf_path) {
    const navBtn = document.getElementById('navViewResumeBtn');
    const modalBtn = document.getElementById('modalViewResumeBtn');
    if (navBtn) navBtn.style.display = 'inline-flex';
    if (modalBtn) modalBtn.style.display = 'inline-flex';
  }
}

// Handle PDF Resume Upload
async function handleResumeUpload(event) {
  const file = event.target.files ? event.target.files[0] : null;
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  document.getElementById('uploadLoader').style.display = 'block';
  document.getElementById('dropZone').style.opacity = '0.5';

  try {
    const res = await fetch('/api/upload-resume', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (res.ok) {
      currentProfileData.resume_profile = data.extracted_profile;
      populateProfileForm(currentProfileData);

      logMessage('AI Agent', `Resume analyzed for ${data.extracted_profile.full_name || 'Candidate'}. Profile synchronized.`);
    } else {
      alert(data.detail || 'Failed to analyze resume PDF.');
    }
  } catch (err) {
    console.error('Error uploading resume:', err);
  } finally {
    document.getElementById('uploadLoader').style.display = 'none';
    document.getElementById('dropZone').style.opacity = '1';
  }
}

// Drag & Drop Setup
function setupDragAndDrop() {
  const dropZone = document.getElementById('dropZone');
  if (!dropZone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--accent-primary)';
      dropZone.style.background = 'rgba(6, 182, 212, 0.1)';
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'rgba(6, 182, 212, 0.4)';
      dropZone.style.background = 'rgba(15, 23, 42, 0.6)';
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      document.getElementById('pdfFileInput').files = files;
      handleResumeUpload({ target: { files: files } });
    }
  });
}

// Save Profile
async function saveProfileAndLaunch(event) {
  event.preventDefault();

  const prof = currentProfileData.resume_profile || {};
  prof.full_name = document.getElementById('profFullName').value.trim();
  prof.email = document.getElementById('profEmail').value.trim();
  prof.phone = document.getElementById('profPhone').value.trim();
  prof.linkedin_url = document.getElementById('profLinkedin').value.trim();
  prof.portfolio_url = document.getElementById('profPortfolio').value.trim();
  prof.location = document.getElementById('profLocation').value.trim();
  prof.last_position = document.getElementById('profLastPosition').value.trim();
  prof.years_experience = parseInt(document.getElementById('profExp').value) || 0;
  prof.skills = document.getElementById('profSkills').value.split(',').map(s => s.trim()).filter(Boolean);
  prof.summary = document.getElementById('profSummary').value.trim();

  currentProfileData.resume_profile = prof;

  try {
    await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentProfileData)
    });

    closeProfileModal();
    logMessage('Profile', 'Candidate profile updated.');
  } catch (err) {
    console.error('Error saving profile:', err);
  }
}

// Fetch stats
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const stats = await res.json();
    document.getElementById('statTotal').innerText = stats.total_discovered || 0;
    document.getElementById('statHighMatch').innerText = stats.high_match_count || 0;
    document.getElementById('statApplied').innerText = stats.applications_submitted || 0;
    document.getElementById('statPortals').innerText = `${stats.platforms_connected || 10} Active`;
  } catch (err) {
    console.error('Error loading stats:', err);
  }
}

// Fetch jobs list
async function loadJobs() {
  try {
    const res = await fetch('/api/jobs');
    allJobsData = await res.json();
    renderJobs();
  } catch (err) {
    console.error('Error loading jobs:', err);
  }
}

// Update Min Score Slider Label
function updateMinScoreLabel(val) {
  document.getElementById('minScoreLabel').innerText = `${val}%`;
}

// Reset Filter UI Controls
function resetFilters() {
  document.getElementById('headerPromptInput').value = '';
  document.getElementById('filterQuery').value = '';
  document.getElementById('filterLocation').value = '';
  document.getElementById('filterSeniority').value = 'All';
  document.getElementById('filterDatePosted').value = '';
  document.getElementById('filterRemoteOnly').checked = false;
  document.getElementById('filterMinScore').value = 40;
  updateMinScoreLabel(40);
  const salaryInput = document.getElementById('filterMinSalary');
  if (salaryInput) salaryInput.value = '';
  const salaryCurr = document.getElementById('filterSalaryCurrency');
  if (salaryCurr) salaryCurr.value = 'INR';
  document.querySelectorAll('input[name="platform"]').forEach(cb => cb.checked = true);
  loadJobs();
}

// Natural Language Prompt Parser & Filter Sync
async function applyPromptAndSearch() {
  const promptInput = document.getElementById('headerPromptInput');
  const promptVal = promptInput ? promptInput.value.trim() : '';
  if (!promptVal) return;

  logMessage('Prompt Engine', `Parsing criteria from prompt: "${promptVal}"...`);

  try {
    const res = await fetch('/api/parse-prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: promptVal })
    });
    const parsed = await res.json();

    // Synchronize UI Controls with parsed criteria
    if (parsed.query) document.getElementById('filterQuery').value = parsed.query;
    if (parsed.locations && parsed.locations.length > 0) {
      document.getElementById('filterLocation').value = parsed.locations.join(', ');
    }
    if (parsed.seniority_level) document.getElementById('filterSeniority').value = parsed.seniority_level;
    if (parsed.date_posted_days) document.getElementById('filterDatePosted').value = String(parsed.date_posted_days);
    if (parsed.remote_only !== undefined) document.getElementById('filterRemoteOnly').checked = parsed.remote_only;
    
    // Synchronize Salary Filter
    if (parsed.min_salary && parsed.min_salary > 0) {
      const salaryInput = document.getElementById('filterMinSalary');
      const salaryCurr = document.getElementById('filterSalaryCurrency');
      if (salaryCurr) salaryCurr.value = parsed.salary_currency || 'INR';
      if (salaryInput) {
        if (parsed.salary_currency === 'INR' && parsed.min_salary >= 100000) {
          salaryInput.value = parsed.min_salary / 100000;
        } else {
          salaryInput.value = parsed.min_salary;
        }
      }
    }

    // Trigger search with parsed criteria
    triggerJobSearch(parsed);
  } catch (err) {
    console.error('Error parsing prompt:', err);
    triggerJobSearch({ prompt: promptVal });
  }
}

// Collect Active Filter Payload
function getFilterPayload() {
  const selectedPlatforms = Array.from(document.querySelectorAll('input[name="platform"]:checked')).map(cb => cb.value);
  const dateVal = document.getElementById('filterDatePosted').value;

  const default10Portals = [
    'company_careers',
    'linkedin',
    'instahyre',
    'naukri',
    'indeed',
    'wellfound',
    'cutshort_hirist',
    'weworkremotely',
    'flexjobs',
    'remote_co'
  ];

  const rawSalary = parseFloat(document.getElementById('filterMinSalary')?.value) || 0;
  const salaryCurr = document.getElementById('filterSalaryCurrency')?.value || 'INR';
  let normalizedMinSalary = rawSalary;
  if (salaryCurr === 'INR' && rawSalary > 0 && rawSalary <= 100) {
    normalizedMinSalary = rawSalary * 100000;
  }

  return {
    prompt: document.getElementById('headerPromptInput').value.trim(),
    query: document.getElementById('filterQuery').value.trim(),
    locations: document.getElementById('filterLocation').value.split(',').map(s => s.trim()).filter(Boolean),
    seniority_level: document.getElementById('filterSeniority').value,
    date_posted_days: dateVal ? parseInt(dateVal) : null,
    remote_only: document.getElementById('filterRemoteOnly').checked,
    platforms: selectedPlatforms.length > 0 ? selectedPlatforms : default10Portals,
    min_fit_score: parseInt(document.getElementById('filterMinScore').value) || 40,
    min_salary: normalizedMinSalary,
    salary_currency: salaryCurr
  };
}

// Trigger Live Multi-Platform Search
async function triggerJobSearch(overridePayload = null) {
  const btn = document.getElementById('searchBtn');
  const stopBtn = document.getElementById('stopBtn');
  const payload = overridePayload || getFilterPayload();

  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Searching Portals...`;
  if (stopBtn) stopBtn.style.display = 'inline-flex';

  try {
    await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    logMessage('System', `Live parallel discovery initiated across ${payload.platforms.length} platforms...`);
  } catch (err) {
    console.error('Error starting job search:', err);
  }
}

// Stop Search Action
async function stopJobSearch() {
  const btn = document.getElementById('searchBtn');
  const stopBtn = document.getElementById('stopBtn');

  try {
    await fetch('/api/stop-search', { method: 'POST' });
    logMessage('System', '🛑 Stop requested. Search halted.');
  } catch (err) {
    console.error('Error stopping search:', err);
  } finally {
    if (stopBtn) stopBtn.style.display = 'none';
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Search 10 Portals`;
    }
  }
}

// Render Job Cards into Grid
function renderJobs() {
  const container = document.getElementById('jobsGrid');
  let filtered = [...allJobsData];

  if (currentFilter === 'HIGH_FIT') {
    filtered = filtered.filter(j => j.match_score >= 50);
  } else if (currentFilter === 'APPLIED') {
    filtered = filtered.filter(j => j.apply_status === 'APPLIED');
  } else if (currentFilter === 'SAVED') {
    filtered = filtered.filter(j => j.apply_status === 'SAVED');
  }

  document.getElementById('jobCount').innerText = filtered.length;

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
        <i class="fa-solid fa-folder-open" style="font-size: 3rem; margin-bottom: 16px;"></i>
        <p style="font-size: 1.1rem; color: var(--text-secondary);">No job listings found in this filter.</p>
        <p style="font-size: 0.85rem; margin-top: 6px;">Click <b>"Search 10 Portals"</b> above or type a prompt like <i>"Remote Senior Python developer"</i> to discover live jobs!</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(job => {
    const score = job.match_score || 0;
    let badgeClass = 'badge-filtered';
    let badgeText = `${score}% Fit`;

    if (score >= 75) {
      badgeClass = 'badge-high';
    } else if (score >= 50) {
      badgeClass = 'badge-medium';
    } else if (score > 0) {
      badgeClass = 'badge-low';
    }

    // Dynamic Matched Technical Skills
    const matchedList = (job.matched_skills && job.matched_skills.length > 0) 
      ? job.matched_skills 
      : (job.tags && job.tags.length > 0 ? job.tags.slice(0, 4) : ['Engineering']);
    const skillsHtml = matchedList.map(s => `<span class="skill-tag">${s}</span>`).join('');

    // Cross-Platform Sources Cluster Badges
    const sourcesList = (job.sources && job.sources.length > 0) 
      ? job.sources 
      : [{ platform: job.platform || 'Portal', url: job.url }];
    
    const isMultiSource = sourcesList.length > 1;
    const sourcesBadgesHtml = sourcesList.map(s => `
      <a href="${s.url}" target="_blank" class="source-badge" title="Open listing on ${s.platform}">
        <i class="fa-solid fa-arrow-up-right-from-square"></i> ${s.platform}
      </a>
    `).join('');

    // Sub-scores rendering
    const sub = job.sub_scores || {};
    const hasSubScores = Object.keys(sub).length > 0;
    const subScoresHtml = hasSubScores ? `
      <div class="sub-scores-container">
        <div class="sub-scores-grid">
          <span class="sub-score-pill">Skill: <strong>${sub.skill_match_40 || 0}/40</strong></span>
          <span class="sub-score-pill">Title: <strong>${sub.title_match_25 || 0}/25</strong></span>
          <span class="sub-score-pill">Level: <strong>${sub.experience_fit_15 || 0}/15</strong></span>
          <span class="sub-score-pill">Salary: <strong>${sub.salary_fit_10 || 0}/10</strong></span>
        </div>
      </div>
    ` : '';

    // Action buttons based on status
    let actionButtonsHtml = '';
    if (job.apply_status === 'APPLIED') {
      const appliedTime = job.applied_at ? ` on ${job.applied_at}` : '';
      actionButtonsHtml = `
        <div class="status-applied">
          <i class="fa-solid fa-circle-check"></i> Applied ${appliedTime}
        </div>
      `;
    } else {
      actionButtonsHtml = `
        <div class="job-card-actions">
          <button class="btn btn-secondary" onclick="updateStatus('${job.job_id}', 'SAVED')" title="Save to Apply Later">
            <i class="fa-solid fa-bookmark"></i> Save
          </button>
          <button class="btn btn-primary" onclick="openDirectPortal('${job.job_id}', '${job.url}')">
            <i class="fa-solid fa-paper-plane"></i> Apply on Portal
          </button>
        </div>
      `;
    }

    return `
      <div class="job-card">
        <div>
          <div class="job-card-header">
            <div>
              <div class="job-title">${job.title}</div>
              <div class="company-name">${job.company}</div>
            </div>
            <div class="match-score-badge ${badgeClass}">
              <i class="fa-solid fa-bolt"></i> ${badgeText}
            </div>
          </div>

          <!-- Metadata Pill Badges -->
          <div class="job-meta-row">
            <span class="meta-pill"><i class="fa-solid fa-location-dot"></i> ${job.location}</span>
            <span class="meta-pill"><i class="fa-solid fa-layer-group"></i> ${job.seniority_level || 'Mid-Level'}</span>
            <span class="meta-pill"><i class="fa-solid fa-clock"></i> ${job.posted_date || 'Recently'}</span>
            <span class="meta-pill"><i class="fa-solid fa-money-bill-wave"></i> ${job.salary || 'Not Disclosed'}</span>
          </div>

          <!-- Cross-Platform Cluster Strip -->
          <div class="sources-cluster-strip">
            <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">
              <i class="fa-solid fa-link"></i> ${isMultiSource ? 'Available on ' + sourcesList.length + ' Portals:' : 'Source Portal:'}
            </span>
            ${sourcesBadgesHtml}
          </div>

          <!-- Explainable AI Fit Sub-scores -->
          ${subScoresHtml}

          <!-- AI Reasoning Summary -->
          <div class="ai-reasoning">
            ${job.reasoning || (job.description ? job.description.slice(0, 180) + '...' : 'Relevant role matching your criteria.')}
          </div>

          <!-- Technical Skills -->
          <div class="skills-tags">
            ${skillsHtml}
          </div>
        </div>

        ${actionButtonsHtml}
      </div>
    `;
  }).join('');
}

// Open Direct Portal Link and ask for status confirmation
async function openDirectPortal(jobId, url) {
  if (url) {
    window.open(url, '_blank');
  }
  const confirmed = confirm(
    "Opening employer job portal in new tab...\n\n" +
    "Once you submit your application on the portal:\n" +
    "• Click 'OK' to mark this job as APPLIED.\n" +
    "• Click 'Cancel' to keep it for later."
  );
  if (confirmed) {
    await updateStatus(jobId, 'APPLIED');
  }
}

// Update Job Status (APPLIED, SAVED, PENDING)
async function updateStatus(jobId, status) {
  try {
    await fetch(`/api/job/${jobId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status })
    });
    logMessage('Tracker', `Job status marked as ${status}.`);
    loadJobs();
    loadStats();
  } catch (err) {
    console.error('Error updating status:', err);
  }
}

// Filter Tab Switch
function filterJobs(status, btnElement) {
  currentFilter = status;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btnElement.classList.add('active');
  renderJobs();
}

// Setup SSE Stream for Live Console Logs
function setupSSEStream() {
  const eventSource = new EventSource('/api/stream');
  const consoleEl = document.getElementById('consoleLogs');

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const msgDiv = document.createElement('div');
    if (data.level === 'SUCCESS') {
      msgDiv.style.color = '#34d399';
    } else if (data.level === 'WARNING') {
      msgDiv.style.color = '#fbbf24';
    }
    msgDiv.innerText = data.message;
    consoleEl.appendChild(msgDiv);
    consoleEl.scrollTop = consoleEl.scrollHeight;

    // Reload jobs list when search completes or halts
    if (data.message.includes('Search Complete') || data.message.includes('Search cancelled') || data.message.includes('Search error') || data.message.includes('Search halted')) {
      loadJobs();
      loadStats();
      const btn = document.getElementById('searchBtn');
      const stopBtn = document.getElementById('stopBtn');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Search 10 Portals`;
      }
      if (stopBtn) stopBtn.style.display = 'none';
    }
  };

  eventSource.onerror = () => {
    document.getElementById('sseStatus').innerText = 'Reconnecting...';
  };
}

function logMessage(source, msg) {
  const consoleEl = document.getElementById('consoleLogs');
  if (!consoleEl) return;
  const msgDiv = document.createElement('div');
  msgDiv.innerText = `[${new Date().toLocaleTimeString()}] [${source}] ${msg}`;
  consoleEl.appendChild(msgDiv);
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

// Modal Handlers
function openProfileModal() {
  document.getElementById('profileModal').classList.add('active');
}

function closeProfileModal() {
  document.getElementById('profileModal').classList.remove('active');
}
