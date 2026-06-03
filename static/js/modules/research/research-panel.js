/**
 * MKM Research Labs - Research Panel Module
 *
 * Handles panel DOM creation, visibility, and event listeners.
 *
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 */
const ResearchPanel = (() => {
  // Private state
  let researchPanelVisible = false;

  const isPDFGeneratorAvailable = () => {
    return typeof ResearchPDFGenerator !== 'undefined';
  };

  /**
   * Create the research panel DOM structure
   */
  const createResearchPanel = () => {
    let panel = document.getElementById('research-panel');
    if (panel) return panel;

    panel = document.createElement('div');
    panel.id = 'research-panel';
    panel.className = 'research-panel hidden';

    panel.innerHTML = `
      <div class="research-panel-header">
        <h3 class="research-panel-title">
          <span class="research-icon">🔬</span>
          Deep Research Results
        </h3>
        <div class="research-panel-actions">
          <button id="toggle-research-details" class="research-toggle-btn" title="Toggle Details">
            <span class="toggle-icon">▼</span>
          </button>
          <button id="close-research-panel" class="research-close-btn" title="Close">×</button>
        </div>
      </div>

      <div class="research-panel-body">
        <div id="research-progress" class="research-progress">
          <div class="research-progress-bar">
            <div id="research-progress-fill" class="research-progress-fill"></div>
          </div>
          <div id="research-progress-text" class="research-progress-text">Initializing...</div>
          <div id="research-progress-steps" class="research-progress-steps"></div>
        </div>

        <div id="research-live-results" class="research-live-results">
          <div class="research-live-header">
            <h4>📊 Live Results</h4>
            <span id="research-live-count" class="research-live-count">0/0 complete</span>
          </div>
          <div id="research-kb-list" class="research-kb-list"></div>
        </div>

        <div id="research-synthesis" class="research-synthesis hidden">
          <div class="research-synthesis-header">
            <h4>📋 Synthesized Answer</h4>
            <div class="research-meta">
              <span id="research-total-sources"></span>
              <span id="research-total-time"></span>
            </div>
          </div>
          <div id="research-synthesis-content" class="research-synthesis-content"></div>

          <div id="research-auto-status" class="research-auto-status"></div>

          <div class="research-actions">
            <button id="copy-synthesis" class="action-button copy-btn">📋 Copy</button>
            <button id="use-in-chat" class="action-button use-btn">💬 Use in Chat</button>
            <button id="download-pdf" class="action-button export-btn" ${!isPDFGeneratorAvailable() ? 'disabled title="PDF module not loaded"' : ''}>📥 Download PDF</button>
          </div>
        </div>
      </div>
    `;

    const chatContainer = document.getElementById('chat-container');
    if (chatContainer && chatContainer.parentNode) {
      chatContainer.parentNode.insertBefore(panel, chatContainer.nextSibling);
    } else {
      document.body.appendChild(panel);
    }

    return panel;
  };

  /**
   * Setup event listeners on the panel
   * @param {Object} handlers - Object containing handler functions
   */
  const setupPanelEventListeners = (handlers = {}) => {
    const panel = document.getElementById('research-panel');
    if (!panel) return;

    const closeBtn = panel.querySelector('#close-research-panel');
    const toggleBtn = panel.querySelector('#toggle-research-details');
    const copyBtn = panel.querySelector('#copy-synthesis');
    const useChatBtn = panel.querySelector('#use-in-chat');
    const downloadBtn = panel.querySelector('#download-pdf');

    if (closeBtn) closeBtn.addEventListener('click', handlers.onClose || hideResearchPanel);
    if (toggleBtn) toggleBtn.addEventListener('click', toggleKBDetails);
    if (copyBtn && handlers.onCopy) copyBtn.addEventListener('click', handlers.onCopy);
    if (useChatBtn && handlers.onUseInChat) useChatBtn.addEventListener('click', handlers.onUseInChat);
    if (downloadBtn && handlers.onDownload) downloadBtn.addEventListener('click', handlers.onDownload);
  };

  /**
   * Show the research panel
   */
  const showResearchPanel = () => {
    const panel = createResearchPanel();
    if (panel) panel.classList.remove('hidden');
    researchPanelVisible = true;
  };

  /**
   * Hide the research panel
   * @param {Function} cleanup - Optional cleanup callback
   */
  const hideResearchPanel = (cleanup) => {
    if (typeof cleanup === 'function') {
      cleanup();
    }
    const panel = document.getElementById('research-panel');
    if (panel) panel.classList.add('hidden');
    researchPanelVisible = false;
  };

  /**
   * Toggle KB details visibility
   */
  const toggleKBDetails = () => {
    const liveResults = document.getElementById('research-live-results');
    const toggleIcon = document.querySelector('#toggle-research-details .toggle-icon');
    if (liveResults) {
      liveResults.classList.toggle('collapsed');
      if (toggleIcon) {
        toggleIcon.textContent = liveResults.classList.contains('collapsed') ? '▶' : '▼';
      }
    }
  };

  /**
   * Reset panel to initial state
   */
  const resetPanel = () => {
    const elements = {
      progressFill: document.getElementById('research-progress-fill'),
      progressText: document.getElementById('research-progress-text'),
      progressSteps: document.getElementById('research-progress-steps'),
      progress: document.getElementById('research-progress'),
      kbList: document.getElementById('research-kb-list'),
      liveCount: document.getElementById('research-live-count'),
      synthesis: document.getElementById('research-synthesis'),
      liveResults: document.getElementById('research-live-results'),
      autoStatus: document.getElementById('research-auto-status')
    };

    if (elements.progressFill) elements.progressFill.style.width = '0%';
    if (elements.progressText) elements.progressText.textContent = 'Initializing...';
    if (elements.progressSteps) elements.progressSteps.innerHTML = '';
    if (elements.progress) elements.progress.classList.remove('hidden');
    if (elements.kbList) elements.kbList.innerHTML = '';
    if (elements.liveCount) elements.liveCount.textContent = '0/0 complete';
    if (elements.synthesis) elements.synthesis.classList.add('hidden');
    if (elements.liveResults) elements.liveResults.classList.remove('hidden', 'collapsed');
    if (elements.autoStatus) elements.autoStatus.innerHTML = '';

    if (isPDFGeneratorAvailable()) {
      ResearchPDFGenerator.clearCache();
    }
  };

  // Public API
  return {
    create: createResearchPanel,
    setupEventListeners: setupPanelEventListeners,
    show: showResearchPanel,
    hide: hideResearchPanel,
    toggle: toggleKBDetails,
    reset: resetPanel,
    isVisible: () => researchPanelVisible,
    setVisible: (visible) => { researchPanelVisible = visible; }
  };
})();
