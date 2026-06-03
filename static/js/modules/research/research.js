/**
 * MKM Research Labs - Research Manager Module
 *
 * Main coordinator that wires up sub-modules and exposes public API.
 *
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 */
const ResearchManager = (() => {
  // Private state
  let isResearchInProgress = false;
  let currentResearchResult = null;

  const isPDFGeneratorAvailable = () => {
    return typeof ResearchPDFGenerator !== 'undefined';
  };

  /**
   * Add the Deep Research button to the query form
   */
  const addResearchButton = () => {
    const queryForm = document.getElementById('query-form');
    if (!queryForm || document.getElementById('research-btn')) return;

    const submitBtn = queryForm.querySelector('button[type="submit"]');
    if (!submitBtn) return;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'research-btn';
    btn.className = 'action-button research-btn';
    btn.innerHTML = '🔬 Deep Research';
    btn.title = 'Query all knowledge bases and synthesize results';

    submitBtn.parentNode.insertBefore(btn, submitBtn.nextSibling);

    btn.addEventListener('click', async () => {
      const query = document.getElementById('query-input')?.value?.trim();
      const model = document.getElementById('model-select')?.value;

      if (!query) {
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('Please enter a research question');
        }
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '🔬 Researching...';

      try {
        await executeResearch(query, model);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '🔬 Deep Research';
      }
    });
  };

  /**
   * Copy synthesized answer to clipboard
   */
  const copySynthesizedAnswer = async () => {
    if (!currentResearchResult) {
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('No research results to copy');
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(currentResearchResult.synthesized_answer);
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Copied to clipboard!');
      }
    } catch (err) {
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Failed to copy');
      }
    }
  };

  /**
   * Download PDF report
   */
  const downloadPDFReport = () => {
    if (!currentResearchResult) {
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('No research results available');
      }
      return;
    }

    if (!isPDFGeneratorAvailable()) {
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('PDF module not loaded');
      }
      return;
    }

    try {
      if (ResearchPDFGenerator.getLastPDF()) {
        const filename = `research_${currentResearchResult.query.substring(0, 30).replace(/[^a-z0-9]/gi, '_')}_${new Date().toISOString().slice(0,10)}.pdf`;
        ResearchPDFGenerator.downloadLast(filename);
      } else {
        ResearchPDFGenerator.generateAndDownload(currentResearchResult);
      }

      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('PDF downloaded!');
      }
    } catch (error) {
      console.error('PDF download error:', error);
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Failed to download PDF: ' + error.message);
      }
    }
  };

  /**
   * Use synthesized answer in chat
   */
  const useSynthesizedAnswerInChat = () => {
    if (!currentResearchResult) {
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('No research results available');
      }
      return;
    }

    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) {
      console.error('Chat container not found');
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Chat container not available');
      }
      return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper';

    const msg = document.createElement('div');
    msg.className = 'message message-assistant research-message';
    msg.innerHTML = `
      <div class="research-message-header">
        <span class="research-badge">🔬 Deep Research</span>
        <span class="research-query-badge">${currentResearchResult.query.substring(0, 50)}${currentResearchResult.query.length > 50 ? '...' : ''}</span>
      </div>
      <div class="research-message-content">${currentResearchResult.synthesized_answer}</div>
      <div class="research-message-meta">
        ${currentResearchResult.total_sources} sources across ${currentResearchResult.kb_results.length} knowledge bases
        • ${(currentResearchResult.total_time_ms/1000).toFixed(1)}s
      </div>
    `;

    wrapper.appendChild(msg);

    try {
      chatContainer.appendChild(wrapper);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch (error) {
      console.error('Error appending to chat:', error);
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Error adding to chat');
      }
      return;
    }

    const chatData = {
      timestamp: new Date().toISOString(),
      type: 'research',
      messages: [
        { role: 'user', content: `[Deep Research Query] ${currentResearchResult.query}` },
        { role: 'assistant', content: currentResearchResult.synthesized_answer },
        { role: 'sources', content: `Sources: ${currentResearchResult.total_sources} across ${currentResearchResult.kb_results.length} knowledge bases` }
      ]
    };

    const savePromise = (typeof ApiService !== 'undefined' && ApiService.saveChat)
      ? ApiService.saveChat(chatData.messages)
      : fetch('/save_chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat: chatData })
        }).then(r => r.json());

    savePromise
      .then(() => {
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('Added to chat and saved');
        }
        if (typeof ChatManager !== 'undefined' && ChatManager.reloadChatHistory) {
          ChatManager.reloadChatHistory();
        }
      })
      .catch(err => {
        console.error('Save failed:', err);
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('Added to chat (save failed)');
        }
      });

    hideResearchPanel();
  };

  /**
   * Show the research panel
   */
  const showResearchPanel = () => {
    if (typeof ResearchPanel !== 'undefined') {
      ResearchPanel.show();
    }
  };

  /**
   * Hide the research panel
   */
  const hideResearchPanel = () => {
    if (typeof ResearchExecutor !== 'undefined') {
      ResearchExecutor.closeConnection();
    }
    if (typeof ResearchPanel !== 'undefined') {
      ResearchPanel.hide();
      ResearchPanel.setVisible(false);
    }
    isResearchInProgress = false;
  };

  /**
   * Execute research query
   * @param {string} query - Research query
   * @param {string} model - Model to use
   * @param {Array} kbKeys - Optional array of KB keys
   * @returns {Promise<Object>} - Research result
   */
  const executeResearch = async (query, model, kbKeys = null) => {
    if (isResearchInProgress) {
      return null;
    }

    isResearchInProgress = true;
    showResearchPanel();

    if (typeof ResearchPanel !== 'undefined') {
      ResearchPanel.reset();
    }

    const callbacks = {
      onStart: () => {
        isResearchInProgress = true;
      },
      onComplete: (result) => {
        currentResearchResult = result;
        isResearchInProgress = false;
      },
      onError: () => {
        isResearchInProgress = false;
      }
    };

    if (typeof ResearchExecutor !== 'undefined') {
      return await ResearchExecutor.execute(query, model, kbKeys, callbacks);
    }

    console.error('ResearchExecutor not available');
    isResearchInProgress = false;
    return null;
  };

  /**
   * Initialize the Research Manager
   */
  const init = () => {
    console.log('Research Manager initialized');

    // Create panel
    if (typeof ResearchPanel !== 'undefined') {
      ResearchPanel.create();
      ResearchPanel.setupEventListeners({
        onClose: hideResearchPanel,
        onCopy: copySynthesizedAnswer,
        onUseInChat: useSynthesizedAnswerInChat,
        onDownload: downloadPDFReport
      });
    }

    // Add research button
    addResearchButton();

    if (!isPDFGeneratorAvailable()) {
      console.warn('ResearchPDFGenerator not loaded - PDF features disabled');
    }
  };

  // Public API
  return {
    init,
    executeResearch,
    showPanel: showResearchPanel,
    hidePanel: hideResearchPanel,
    getResult: () => currentResearchResult,
    copySynthesizedAnswer,
    downloadPDF: downloadPDFReport,
    useInChat: useSynthesizedAnswerInChat,
    isInProgress: () => isResearchInProgress
  };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => ResearchManager.init());
} else {
  ResearchManager.init();
}
