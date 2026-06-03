/**
 * MKM Research Labs - Research Executor Module
 *
 * Handles streaming/fallback execution logic and auto-actions.
 *
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 */
const ResearchExecutor = (() => {
  // Private state
  let eventSource = null;
  let connectionTimeout = null;

  const CONNECTION_TIMEOUT_MS = 30000;

  const isPDFGeneratorAvailable = () => {
    return typeof ResearchPDFGenerator !== 'undefined';
  };

  const clearConnectionTimeout = () => {
    if (connectionTimeout) {
      clearTimeout(connectionTimeout);
      connectionTimeout = null;
    }
  };

  /**
   * Close the current event source connection
   */
  const closeConnection = () => {
    clearConnectionTimeout();
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };

  /**
   * Save research result to chat history
   * @param {Object} result - Research result object
   * @returns {Promise<boolean>} - Success status
   */
  const saveResearchToHistory = async (result) => {
    try {
      const researchChat = {
        timestamp: result.timestamp,
        type: 'research',
        query: result.query,
        model: result.model,
        messages: [
          { role: 'user', content: `[Deep Research Query] ${result.query}` },
          { role: 'assistant', content: result.synthesized_answer },
          { role: 'research_details', content: JSON.stringify({
              kb_results: result.kb_results,
              total_sources: result.total_sources,
              total_time_ms: result.total_time_ms
            })
          }
        ]
      };

      const response = await fetch('/save_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat: researchChat })
      });

      const data = await response.json();

      if (response.ok) {
        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.addAutoStatus('save', true, 'Saved to history');
        }
        return true;
      } else {
        throw new Error(data.error || 'Failed to save');
      }
    } catch (error) {
      console.error('Failed to save research:', error);
      if (typeof ResearchProgress !== 'undefined') {
        ResearchProgress.addAutoStatus('save', false, `Save failed: ${error.message}`);
      }
      return false;
    }
  };

  /**
   * Auto-generate PDF report
   * @param {Object} result - Research result object
   * @returns {boolean} - Success status
   */
  const autoGeneratePDF = (result) => {
    if (!isPDFGeneratorAvailable()) {
      if (typeof ResearchProgress !== 'undefined') {
        ResearchProgress.addAutoStatus('pdf', false, 'PDF module not loaded');
      }
      return false;
    }

    try {
      const pdf = ResearchPDFGenerator.generate(result);
      if (pdf) {
        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.addAutoStatus('pdf', true, 'PDF report ready');
        }
        return true;
      } else {
        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.addAutoStatus('pdf', false, 'PDF generation failed');
        }
        return false;
      }
    } catch (error) {
      console.error('PDF generation error:', error);
      if (typeof ResearchProgress !== 'undefined') {
        ResearchProgress.addAutoStatus('pdf', false, `PDF error: ${error.message}`);
      }
      return false;
    }
  };

  /**
   * Execute research using SSE streaming
   * @param {string} query - Research query
   * @param {string} model - Model to use
   * @param {Array} kbKeys - Optional array of KB keys to query
   * @param {Object} callbacks - Callback functions for state management
   * @returns {Promise<Object>} - Research result
   */
  const executeResearchStreaming = (query, model, kbKeys = null, callbacks = {}) => {
    return new Promise((resolve, reject) => {
      const { onStart, onComplete, onError } = callbacks;

      if (onStart) onStart();

      let url = `/research_query_stream?query=${encodeURIComponent(query)}&model=${encodeURIComponent(model)}`;
      if (kbKeys?.length) {
        url += `&kb_keys=${encodeURIComponent(kbKeys.join(','))}`;
      }

      eventSource = new EventSource(url);
      let totalKBs = 0;
      let connectionEstablished = false;

      connectionTimeout = setTimeout(() => {
        if (!connectionEstablished && eventSource) {
          eventSource.close();
          eventSource = null;
          if (onError) onError();
          reject(new Error('Connection timeout - server not responding'));
        }
      }, CONNECTION_TIMEOUT_MS);

      eventSource.addEventListener('start', (e) => {
        connectionEstablished = true;
        clearConnectionTimeout();

        const data = JSON.parse(e.data);
        totalKBs = data.total_kbs;

        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.initLiveCount(totalKBs);
          ResearchProgress.initProgressSteps(data.kb_names);
          ResearchProgress.updateProgressBar(0, totalKBs, `Starting research across ${totalKBs} knowledge bases...`);
        }
      });

      eventSource.addEventListener('querying', (e) => {
        const data = JSON.parse(e.data);
        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.updateProgressBar(data.step - 1, totalKBs, `Querying ${data.kb_name}... (${data.step}/${data.total})`);
          ResearchProgress.updateProgressStep(data.kb_key, 'querying');
        }
      });

      eventSource.addEventListener('kb_complete', (e) => {
        const data = JSON.parse(e.data);
        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.updateProgressStep(data.kb_key, data.result.success ? 'success' : 'error', data.result.query_time_ms);
          ResearchProgress.addKBResultCard(data.result);
          ResearchProgress.updateProgressBar(data.step, totalKBs, `Completed ${data.kb_name} (${data.step}/${data.total})`);
        }
      });

      eventSource.addEventListener('synthesizing', () => {
        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.updateProgressBar(totalKBs, totalKBs, 'Synthesizing responses...');
        }
      });

      eventSource.addEventListener('complete', async (e) => {
        clearConnectionTimeout();
        const result = JSON.parse(e.data);

        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.showSynthesis(result);
        }

        eventSource.close();
        eventSource = null;

        if (onComplete) onComplete(result);

        await saveResearchToHistory(result);
        autoGeneratePDF(result);

        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('Research complete!');
        }
        resolve(result);
      });

      eventSource.addEventListener('error', (e) => {
        clearConnectionTimeout();
        let errorMsg = 'Connection error';
        try {
          if (e.data) errorMsg = JSON.parse(e.data).error || errorMsg;
        } catch {}

        eventSource.close();
        eventSource = null;

        if (onError) onError();

        if (typeof ResearchProgress !== 'undefined') {
          ResearchProgress.showError(errorMsg);
        }

        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification(`Research failed: ${errorMsg}`);
        }
        reject(new Error(errorMsg));
      });

      eventSource.onerror = () => {
        clearConnectionTimeout();
        if (eventSource?.readyState === EventSource.CLOSED) return;
        eventSource?.close();
        eventSource = null;
        if (onError) onError();
        reject(new Error('Lost connection to server'));
      };
    });
  };

  /**
   * Execute research using POST fallback
   * @param {string} query - Research query
   * @param {string} model - Model to use
   * @param {Array} kbKeys - Optional array of KB keys to query
   * @param {Object} callbacks - Callback functions for state management
   * @returns {Promise<Object>} - Research result
   */
  const executeResearchFallback = async (query, model, kbKeys = null, callbacks = {}) => {
    const { onStart, onComplete, onError } = callbacks;

    if (onStart) onStart();

    try {
      const payload = { query, model };
      if (kbKeys?.length) payload.kb_keys = kbKeys;

      if (typeof ResearchProgress !== 'undefined') {
        ResearchProgress.updateProgressBar(0, 5, 'Querying all knowledge bases...');
      }

      const response = await fetch('/research_query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.status === 404) {
        throw new Error('Research endpoint not available');
      }

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Server returned ${response.status}`);

      if (typeof ResearchProgress !== 'undefined') {
        result.kb_results?.forEach(r => ResearchProgress.addKBResultCard(r));
        ResearchProgress.showSynthesis(result);
      }

      if (onComplete) onComplete(result);

      await saveResearchToHistory(result);
      autoGeneratePDF(result);

      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification('Research complete!');
      }
      return result;

    } catch (error) {
      console.error('Research failed:', error);
      if (typeof UI !== 'undefined' && UI.showNotification) {
        UI.showNotification(`Research failed: ${error.message}`);
      }

      if (typeof ResearchProgress !== 'undefined') {
        ResearchProgress.showError(error.message);
      }

      if (onError) onError();
      return null;
    }
  };

  /**
   * Execute research with streaming, falling back to POST
   * @param {string} query - Research query
   * @param {string} model - Model to use
   * @param {Array} kbKeys - Optional array of KB keys to query
   * @param {Object} callbacks - Callback functions for state management
   * @returns {Promise<Object>} - Research result
   */
  const executeResearch = async (query, model, kbKeys = null, callbacks = {}) => {
    try {
      return await executeResearchStreaming(query, model, kbKeys, callbacks);
    } catch (streamError) {
      console.warn('Streaming failed, using fallback:', streamError);
      return await executeResearchFallback(query, model, kbKeys, callbacks);
    }
  };

  // Public API
  return {
    execute: executeResearch,
    executeStreaming: executeResearchStreaming,
    executeFallback: executeResearchFallback,
    closeConnection,
    saveToHistory: saveResearchToHistory,
    generatePDF: autoGeneratePDF
  };
})();
