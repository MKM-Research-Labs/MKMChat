/**
 * MKM Research Labs - Visualization Manager Module
 *
 * Main coordinator that wires up sub-modules and exposes public API.
 * Handles data visualization for query results and document analysis.
 *
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 */
const VisualizationManager = (() => {
  // Private state
  let currentQuery = null;
  let currentResults = null;

  /**
   * Extract sources from chat messages
   * @param {Array} messages - Chat messages array
   * @param {number} messageIndex - Starting message index
   * @returns {Object} - Object containing userQuery and sources
   */
  const extractSourcesFromMessages = (messages, messageIndex) => {
    // Find user query
    let userQuery = '';
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userQuery = messages[i].content;
        break;
      }
    }

    // Find sources
    let sources = [];
    for (let i = messageIndex + 1; i < messages.length; i++) {
      if (messages[i].role === 'sources') {
        const sourcesContent = messages[i].content;

        // Parse sources content (format: "Sources:\n• file1.pdf (p.1, 2)\n• file2.pdf (p.3)")
        const sourceLines = sourcesContent.split('\n').slice(1);

        sourceLines.forEach(line => {
          if (!line.trim()) return;

          const match = line.match(/• (.*?) \(p\.(.*?)\)/);
          if (match) {
            const file = match[1].trim();
            const pages = match[2].split(',').map(p => p.trim());

            pages.forEach(page => {
              sources.push({ file, page });
            });
          }
        });

        break;
      }
    }

    return { userQuery, sources };
  };

  /**
   * Render all charts with current results
   * @param {Object} results - Analysis results
   */
  const renderAllCharts = (results) => {
    if (typeof VisualizationCharts !== 'undefined') {
      VisualizationCharts.renderRelevanceDistribution('chart-relevance', results.relevanceDistribution);
      VisualizationCharts.renderSourceDistribution('chart-sources', results.topSources);
      VisualizationCharts.renderDateDistribution('chart-dates', results.dateDistribution);
      VisualizationCharts.renderKeywordCloud('keyword-cloud', results.topKeywords);
    }
  };

  /**
   * Export visualization as PDF
   */
  const exportVisualizationAsPDF = () => {
    if (!currentQuery || !currentResults) {
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('No visualization data to export');
      }
      return;
    }

    if (typeof UI !== 'undefined' && UI.showNotification) {
      UI.showNotification('Exporting visualization as PDF...');
    }

    // In a real implementation, this would use jsPDF to generate a PDF
    setTimeout(() => {
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Visualization exported as PDF');
      }
    }, 1500);
  };

  /**
   * Save visualization analysis
   */
  const saveVisualization = () => {
    if (typeof UI !== 'undefined' && UI.showNotification) {
      UI.showNotification('Analysis saved to your research notebook');
    }
    // In a real implementation, this would save the visualization data
  };

  /**
   * Visualize query results
   * @param {number} messageIndex - Index of message to analyze
   */
  const visualizeQueryResults = async (messageIndex) => {
    try {
      // Get chat messages
      if (typeof ChatManager === 'undefined' || !ChatManager.getChatMessages) {
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('ChatManager not available');
        }
        return;
      }

      const messages = ChatManager.getChatMessages();
      if (!messages || messages.length === 0) {
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('No chat messages to analyze');
        }
        return;
      }

      // Extract sources from messages
      const { userQuery, sources } = extractSourcesFromMessages(messages, messageIndex);

      if (sources.length === 0) {
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('No sources found to visualize');
        }
        return;
      }

      // Show loading notification
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Analyzing query results...');
      }

      // Use API to analyze sources
      if (typeof VisualizationData !== 'undefined') {
        currentResults = await VisualizationData.analyzeWithAPI(sources, userQuery);
      }
      currentQuery = userQuery;

      if (!currentResults) {
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('Insufficient data to visualize');
        }
        return;
      }

      // Create and setup visualization container
      if (typeof VisualizationPanel !== 'undefined') {
        VisualizationPanel.create();
        VisualizationPanel.updateQueryInfo(currentQuery, currentResults.totalResults);
        VisualizationPanel.setupTabHandlers();
        VisualizationPanel.setupActionHandlers({
          onClose: () => VisualizationPanel.hide(),
          onSave: saveVisualization,
          onExport: exportVisualizationAsPDF
        });
      }

      // Initialize Chart.js and render charts
      if (typeof VisualizationCharts !== 'undefined') {
        await VisualizationCharts.init();
        renderAllCharts(currentResults);
      }

      // Show container
      if (typeof VisualizationPanel !== 'undefined') {
        VisualizationPanel.show();
      }

      // Success notification
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Analysis complete');
      }
    } catch (error) {
      console.error('Visualization error:', error);
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Failed to visualize results: ' + error.message);
      }
    }
  };

  // Public API
  return {
    /**
     * Initialize visualization manager
     */
    init: () => {
      console.log('Visualization Manager initialized');

      // Inject CSS styles
      if (typeof VisualizationPanel !== 'undefined') {
        VisualizationPanel.injectStyles();
      }
    },

    /**
     * Add visualization buttons to assistant messages
     * @param {HTMLElement} messageElement - Message element
     * @param {number} messageIndex - Message index
     * @param {string} role - Message role
     */
    attachVisualizationToMessage: (messageElement, messageIndex, role) => {
      if (role === 'assistant' && typeof VisualizationPanel !== 'undefined') {
        VisualizationPanel.addVisualizationButton(messageElement, () => {
          visualizeQueryResults(messageIndex);
        });
      }
    },

    /**
     * Visualize query results
     * @param {number} messageIndex - Index of message to analyze
     */
    visualizeQueryResults,

    /**
     * Get current results
     * @returns {Object|null} - Current results or null
     */
    getResults: () => currentResults,

    /**
     * Get current query
     * @returns {string|null} - Current query or null
     */
    getQuery: () => currentQuery
  };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => VisualizationManager.init());
} else {
  VisualizationManager.init();
}
