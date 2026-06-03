/**
 * MKM Research Labs - Visualization Panel Module
 *
 * Handles DOM creation and panel visibility for visualizations.
 *
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 */
const VisualizationPanel = (() => {

  /**
   * Create visualization container in DOM
   * @returns {HTMLElement} - Visualization container element
   */
  const createVisualizationContainer = () => {
    // Check if container already exists
    let vizContainer = document.getElementById('query-visualization-container');
    if (vizContainer) {
      return vizContainer;
    }

    // Create container
    vizContainer = document.createElement('div');
    vizContainer.id = 'query-visualization-container';
    vizContainer.className = 'bg-white rounded-lg shadow-lg p-4 mb-4 hidden';

    // Create header
    const header = document.createElement('div');
    header.className = 'mb-6';
    header.innerHTML = `
      <h2 class="text-xl font-bold">Query Analysis: <span id="viz-query-term"></span></h2>
      <p class="text-gray-600"><span id="viz-result-count"></span> results found</p>
    `;

    // Create tabs
    const tabs = document.createElement('div');
    tabs.className = 'flex border-b mb-4';
    tabs.innerHTML = `
      <button id="tab-relevance" class="viz-tab active px-4 py-2 border-b-2 border-blue-500 text-blue-600">Relevance</button>
      <button id="tab-sources" class="viz-tab px-4 py-2 text-gray-500">Sources</button>
      <button id="tab-dates" class="viz-tab px-4 py-2 text-gray-500">Dates</button>
      <button id="tab-keywords" class="viz-tab px-4 py-2 text-gray-500">Keywords</button>
    `;

    // Create content panels
    const content = document.createElement('div');
    content.className = 'py-4';
    content.innerHTML = `
      <div id="panel-relevance" class="viz-panel">
        <div class="w-full h-64">
          <canvas id="chart-relevance"></canvas>
        </div>
      </div>
      <div id="panel-sources" class="viz-panel hidden">
        <div class="w-full h-64">
          <canvas id="chart-sources"></canvas>
        </div>
      </div>
      <div id="panel-dates" class="viz-panel hidden">
        <div class="w-full h-64">
          <canvas id="chart-dates"></canvas>
        </div>
      </div>
      <div id="panel-keywords" class="viz-panel hidden">
        <div id="keyword-cloud" class="w-full min-h-32 p-4 bg-gray-100 rounded-lg flex flex-wrap justify-center"></div>
      </div>
    `;

    // Create footer with actions
    const footer = document.createElement('div');
    footer.className = 'mt-4 flex justify-between items-center';
    footer.innerHTML = `
      <button id="close-visualization" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">
        Close
      </button>
      <div>
        <button id="save-visualization" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 mr-2">
          Save Analysis
        </button>
        <button id="export-visualization" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
          Export PDF
        </button>
      </div>
    `;

    // Assemble container
    vizContainer.appendChild(header);
    vizContainer.appendChild(tabs);
    vizContainer.appendChild(content);
    vizContainer.appendChild(footer);

    // Attach to chat container's parent
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer && chatContainer.parentNode) {
      chatContainer.parentNode.insertBefore(vizContainer, chatContainer.nextSibling);
    }

    return vizContainer;
  };

  /**
   * Show the visualization container
   */
  const show = () => {
    const container = document.getElementById('query-visualization-container');
    if (container) {
      container.classList.remove('hidden');
    }
  };

  /**
   * Hide the visualization container
   */
  const hide = () => {
    const container = document.getElementById('query-visualization-container');
    if (container) {
      container.classList.add('hidden');
    }
  };

  /**
   * Update the query info display
   * @param {string} query - Query text
   * @param {number} resultCount - Number of results
   */
  const updateQueryInfo = (query, resultCount) => {
    const queryEl = document.getElementById('viz-query-term');
    const countEl = document.getElementById('viz-result-count');

    if (queryEl) queryEl.textContent = `"${query}"`;
    if (countEl) countEl.textContent = resultCount;
  };

  /**
   * Setup tab click handlers
   */
  const setupTabHandlers = () => {
    document.querySelectorAll('.viz-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        // Update active tab
        document.querySelectorAll('.viz-tab').forEach(t => {
          t.classList.remove('active', 'border-b-2', 'border-blue-500', 'text-blue-600');
          t.classList.add('text-gray-500');
        });
        tab.classList.add('active', 'border-b-2', 'border-blue-500', 'text-blue-600');
        tab.classList.remove('text-gray-500');

        // Show corresponding panel
        const panelId = `panel-${tab.id.split('-')[1]}`;
        document.querySelectorAll('.viz-panel').forEach(panel => {
          panel.classList.add('hidden');
        });
        document.getElementById(panelId).classList.remove('hidden');

        // Resize charts to fix rendering issues
        window.dispatchEvent(new Event('resize'));
      });
    });
  };

  /**
   * Setup action button handlers
   * @param {Object} handlers - Object containing handler functions
   */
  const setupActionHandlers = (handlers = {}) => {
    const closeBtn = document.getElementById('close-visualization');
    const saveBtn = document.getElementById('save-visualization');
    const exportBtn = document.getElementById('export-visualization');

    if (closeBtn) {
      closeBtn.addEventListener('click', handlers.onClose || hide);
    }

    if (saveBtn && handlers.onSave) {
      saveBtn.addEventListener('click', handlers.onSave);
    }

    if (exportBtn && handlers.onExport) {
      exportBtn.addEventListener('click', handlers.onExport);
    }
  };

  /**
   * Add visualization button to chat message
   * @param {HTMLElement} messageElement - Message element
   * @param {Function} onClick - Click handler
   */
  const addVisualizationButton = (messageElement, onClick) => {
    // Check if button already exists
    if (messageElement.querySelector('.visualize-btn')) {
      return;
    }

    // Create button
    const button = document.createElement('button');
    button.className = 'visualize-btn absolute top-2 right-2 bg-purple-500 text-white px-2 py-1 rounded text-sm hover:bg-purple-600 transition-colors';
    button.textContent = 'Visualize';
    button.onclick = (e) => {
      e.preventDefault();
      if (onClick) onClick();
    };

    // Add button to message
    messageElement.appendChild(button);
  };

  /**
   * Inject CSS styles for visualization elements
   */
  const injectStyles = () => {
    const style = document.createElement('style');
    style.textContent = `
      .visualize-btn {
        opacity: 0;
        transition: opacity 0.2s;
      }
      .message-wrapper:hover .visualize-btn {
        opacity: 1;
      }
    `;
    document.head.appendChild(style);
  };

  // Public API
  return {
    create: createVisualizationContainer,
    show,
    hide,
    updateQueryInfo,
    setupTabHandlers,
    setupActionHandlers,
    addVisualizationButton,
    injectStyles
  };
})();
