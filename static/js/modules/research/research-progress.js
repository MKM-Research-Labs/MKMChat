/**
 * MKM Research Labs - Research Progress Module
 *
 * Handles progress tracking, step indicators, and result cards.
 *
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 */
const ResearchProgress = (() => {

  /**
   * Initialize progress steps for each knowledge base
   * @param {Object} kbNames - Object mapping kb_key to display name
   */
  const initProgressSteps = (kbNames) => {
    const progressSteps = document.getElementById('research-progress-steps');
    if (!progressSteps) return;

    progressSteps.innerHTML = '';
    Object.entries(kbNames).forEach(([key, name], index) => {
      const step = document.createElement('div');
      step.className = 'progress-step-item';
      step.id = `progress-step-${key}`;
      step.innerHTML = `
        <span class="step-number">${index + 1}</span>
        <span class="step-name">${name}</span>
        <span class="step-status">⏳</span>
      `;
      progressSteps.appendChild(step);
    });
  };

  /**
   * Update a progress step's status
   * @param {string} kbKey - Knowledge base key
   * @param {string} status - Status: 'querying', 'success', 'error'
   * @param {number} timeMs - Optional time in milliseconds
   */
  const updateProgressStep = (kbKey, status, timeMs = null) => {
    const step = document.getElementById(`progress-step-${kbKey}`);
    if (!step) return;

    const statusEl = step.querySelector('.step-status');
    if (!statusEl) return;

    step.classList.remove('active', 'complete', 'error');

    switch (status) {
      case 'querying':
        step.classList.add('active');
        statusEl.innerHTML = '<span class="spinner">⟳</span>';
        break;
      case 'success':
        step.classList.add('complete');
        statusEl.textContent = `✓ ${timeMs ? (timeMs/1000).toFixed(1) + 's' : ''}`;
        break;
      case 'error':
        step.classList.add('error');
        statusEl.textContent = '✗';
        break;
    }
  };

  /**
   * Update the progress bar
   * @param {number} current - Current step number
   * @param {number} total - Total number of steps
   * @param {string} message - Status message to display
   */
  const updateProgressBar = (current, total, message) => {
    const progressFill = document.getElementById('research-progress-fill');
    const progressText = document.getElementById('research-progress-text');

    if (progressFill) {
      progressFill.style.width = `${(current / (total + 1)) * 100}%`;
    }
    if (progressText) {
      progressText.textContent = message;
    }
  };

  /**
   * Update live count display
   * @param {number} total - Total number of knowledge bases
   */
  const initLiveCount = (total) => {
    const liveCount = document.getElementById('research-live-count');
    if (liveCount) liveCount.textContent = `0/${total} complete`;
  };

  /**
   * Add a knowledge base result card
   * @param {Object} result - KB result object
   */
  const addKBResultCard = (result) => {
    const kbList = document.getElementById('research-kb-list');
    if (!kbList) return;

    const card = document.createElement('div');
    card.className = `research-kb-card ${result.success ? 'success' : 'error'}`;
    card.id = `kb-card-${result.kb_key}`;

    const previewLength = 200;
    const responsePreview = result.response && result.response.length > previewLength
      ? result.response.substring(0, previewLength) + '...'
      : result.response || 'No response';

    card.innerHTML = `
      <div class="kb-card-header" onclick="this.parentElement.classList.toggle('expanded')">
        <div class="kb-card-title">
          <span class="kb-status ${result.success ? 'status-success' : 'status-error'}">${result.success ? '✓' : '✗'}</span>
          <span class="kb-name">${result.kb_name}</span>
        </div>
        <div class="kb-card-meta">
          <span class="kb-doc-count">${result.doc_count || 0} docs</span>
          <span class="kb-time">${((result.query_time_ms || 0)/1000).toFixed(1)}s</span>
          <span class="kb-expand-icon">▶</span>
        </div>
      </div>
      <div class="kb-card-preview">${responsePreview}</div>
      <div class="kb-card-body">
        ${result.success ? `
          <div class="kb-response">${result.response}</div>
          ${result.sources?.length ? `
            <div class="kb-sources">
              <strong>Sources:</strong>
              <ul>${result.sources.map(s => `<li>${s.file} (p.${s.page})</li>`).join('')}</ul>
            </div>
          ` : ''}
        ` : `<div class="kb-error">${result.error || 'Unknown error'}</div>`}
      </div>
    `;

    kbList.appendChild(card);

    // Update live count
    const liveCount = document.getElementById('research-live-count');
    if (liveCount) {
      const completed = kbList.querySelectorAll('.research-kb-card').length;
      const match = liveCount.textContent.match(/\/(\d+)/);
      liveCount.textContent = `${completed}/${match ? match[1] : '?'} complete`;
    }
  };

  /**
   * Show the synthesis section with results
   * @param {Object} result - Research result object
   */
  const showSynthesis = (result) => {
    const synthesis = document.getElementById('research-synthesis');
    const content = document.getElementById('research-synthesis-content');
    const totalSources = document.getElementById('research-total-sources');
    const totalTime = document.getElementById('research-total-time');
    const progress = document.getElementById('research-progress');

    if (synthesis) synthesis.classList.remove('hidden');
    if (content) content.textContent = result.synthesized_answer;
    if (totalSources) totalSources.textContent = `${result.total_sources} sources`;
    if (totalTime) totalTime.textContent = `${(result.total_time_ms/1000).toFixed(1)}s total`;
    if (progress) progress.classList.add('hidden');
  };

  /**
   * Show an error in the synthesis section
   * @param {string} errorMsg - Error message to display
   */
  const showError = (errorMsg) => {
    const content = document.getElementById('research-synthesis-content');
    const synthesis = document.getElementById('research-synthesis');
    if (content && synthesis) {
      synthesis.classList.remove('hidden');
      content.innerHTML = `<div class="research-error">Error: ${errorMsg}</div>`;
    }
  };

  /**
   * Add an auto-status message
   * @param {string} type - Status type identifier
   * @param {boolean} success - Whether the action succeeded
   * @param {string} message - Status message
   */
  const addAutoStatus = (type, success, message) => {
    const autoStatus = document.getElementById('research-auto-status');
    if (!autoStatus) return;

    const item = document.createElement('div');
    item.className = `auto-status-item ${success ? 'success' : 'error'}`;
    item.innerHTML = `
      <span class="status-icon">${success ? '✓' : '✗'}</span>
      <span class="status-text">${message}</span>
    `;
    autoStatus.appendChild(item);
  };

  // Public API
  return {
    initProgressSteps,
    updateProgressStep,
    updateProgressBar,
    initLiveCount,
    addKBResultCard,
    showSynthesis,
    showError,
    addAutoStatus
  };
})();
