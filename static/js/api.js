/**
 * MKM Research Labs - API Service
 * 
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 * 
 * This software is provided under license by MKM Research Labs. 
 * Use, reproduction, distribution, or modification of this code is subject to the 
 * terms and conditions of the license agreement provided with this software.
 *
 * Handles all API communication with the backend
 * 
 * FIXED ISSUES:
 * - Added research_query_stream endpoint
 * - Added better error handling
 * - Added request timeout support
 */
const ApiService = (() => {
    // Private properties
    const apiEndpoints = {
      query: '/query',
      saveChat: '/save_chat',
      getChats: '/get_chats',
      deleteChat: '/delete_chat',
      getSummarizedFiles: '/get_summarised_files',
      getAvailableIndices: '/get_available_indices',
      switchIndex: '/switch_index',
      // Research endpoints
      researchQuery: '/research_query',
      researchQueryStream: '/research_query_stream',
      // Analysis endpoint
      analyzeSources: '/analyze_sources'
    };
    
    // Default request timeout (30 seconds)
    const DEFAULT_TIMEOUT = 30000;
  
    /**
     * Make API request with timeout support
     * @param {string} url - API endpoint
     * @param {string} method - HTTP method
     * @param {Object} data - Request payload (for POST)
     * @param {number} timeout - Request timeout in ms
     * @returns {Promise} - Promise with response data
     */
    const makeRequest = async (url, method = 'GET', data = null, timeout = DEFAULT_TIMEOUT) => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      try {
        const options = {
          method,
          headers: {
            'Content-Type': 'application/json'
          },
          signal: controller.signal
        };
  
        if (data && method !== 'GET') {
          options.body = JSON.stringify(data);
        }
  
        const response = await fetch(url, options);
        clearTimeout(timeoutId);
        
        // Parse JSON response
        const responseData = await response.json();
        
        // Check for API error
        if (!response.ok) {
          throw new Error(responseData.error || `Server returned ${response.status}`);
        }
        
        return responseData;
      } catch (error) {
        clearTimeout(timeoutId);
        
        // Handle abort (timeout)
        if (error.name === 'AbortError') {
          throw new Error('Request timeout - server did not respond');
        }
        
        console.error(`API Error (${url}):`, error);
        throw error;
      }
    };
    
    /**
     * Check if an endpoint exists (doesn't return 404)
     * @param {string} url - Endpoint to check
     * @returns {Promise<boolean>} - True if endpoint exists
     */
    const checkEndpointExists = async (url) => {
      try {
        const response = await fetch(url, { method: 'HEAD' });
        return response.status !== 404;
      } catch (error) {
        return false;
      }
    };
  
    // Public methods
    return {
      /**
       * Get all endpoint URLs (for debugging)
       * @returns {Object} - Endpoint definitions
       */
      getEndpoints: () => ({ ...apiEndpoints }),
      
      /**
       * Send query to the LLM
       * @param {string} query - User query text
       * @param {string} model - Selected model name
       * @returns {Promise} - Promise with response and sources
       */
      sendQuery: (query, model) => {
        return makeRequest(apiEndpoints.query, 'POST', { query, model });
      },
  
      /**
       * Save chat history
       * @param {Array} messages - Chat messages
       * @returns {Promise} - Promise with save status
       */
      saveChat: (messages) => {
        return makeRequest(apiEndpoints.saveChat, 'POST', {
          timestamp: new Date().toISOString(),
          messages: messages
        });
      },
  
      /**
       * Get chat history
       * @returns {Promise} - Promise with chat history
       */
      getChats: () => {
        return makeRequest(apiEndpoints.getChats);
      },
  
      /**
       * Delete a chat by ID
       * @param {string} chatId - Chat ID to delete
       * @returns {Promise} - Promise with delete status
       */
      deleteChat: (chatId) => {
        return makeRequest(`${apiEndpoints.deleteChat}/${chatId}`, 'DELETE');
      },

      /**
       * Get document summaries
       * @param {string} knowledgeBase - Optional knowledge base key (e.g., 'misc', 'phys', 'pops')
       * @returns {Promise} - Promise with document summaries
       */
      getDocumentSummaries: (knowledgeBase = null) => {
        let url = apiEndpoints.getSummarizedFiles;
        if (knowledgeBase) {
          url += `?docs_type=${encodeURIComponent(knowledgeBase)}`;
        }
        return makeRequest(url);
      },
  
      /**
       * Get available knowledge bases
       * @returns {Promise} - Promise with knowledge base info
       */
      getKnowledgeBases: () => {
        return makeRequest(apiEndpoints.getAvailableIndices);
      },
  
      /**
       * Switch active knowledge base
       * @param {string} indexKey - Knowledge base key to switch to
       * @returns {Promise} - Promise with switch status
       */
      switchKnowledgeBase: (indexKey) => {
        return makeRequest(apiEndpoints.switchIndex, 'POST', { index_key: indexKey });
      },
      
      /**
       * Send research query across all knowledge bases (non-streaming)
       * @param {string} query - Research question
       * @param {string} model - Selected model
       * @param {Array} kbKeys - Optional array of specific KB keys
       * @returns {Promise} - Promise with research results
       */
      sendResearchQuery: (query, model, kbKeys = null) => {
        const payload = { query, model };
        if (kbKeys) {
          payload.kb_keys = kbKeys;
        }
        // Longer timeout for research queries (5 minutes)
        return makeRequest(apiEndpoints.researchQuery, 'POST', payload, 300000);
      },
      
      /**
       * Get the streaming research query URL
       * @param {string} query - Research question
       * @param {string} model - Selected model
       * @param {Array} kbKeys - Optional array of specific KB keys
       * @returns {string} - URL for EventSource connection
       */
      getResearchStreamUrl: (query, model, kbKeys = null) => {
        let url = `${apiEndpoints.researchQueryStream}?query=${encodeURIComponent(query)}&model=${encodeURIComponent(model)}`;
        if (kbKeys && kbKeys.length > 0) {
          url += `&kb_keys=${encodeURIComponent(kbKeys.join(','))}`;
        }
        return url;
      },
      
      /**
       * Analyze sources for visualization
       * @param {Array} sources - Source data
       * @param {string} query - Original query
       * @returns {Promise} - Promise with analysis results
       */
      analyzeSources: (sources, query) => {
        return makeRequest(apiEndpoints.analyzeSources, 'POST', { sources, query });
      },
      
      /**
       * Check if research endpoints are available
       * @returns {Promise<boolean>} - True if research is available
       */
      isResearchAvailable: async () => {
        try {
          // Try a simple OPTIONS request to check if endpoint exists
          const response = await fetch(apiEndpoints.researchQuery, { method: 'OPTIONS' });
          return response.status !== 404;
        } catch (error) {
          return false;
        }
      }
    };
  })();
