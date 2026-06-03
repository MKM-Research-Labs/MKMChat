/**
 * MKM Research Labs - Document Management
 * 
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 * 
 * This software is provided under license by MKM Research Labs. 
 * Use, reproduction, distribution, or modification of this code is subject to the 
 * terms and conditions of the license agreement provided with this software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.


 * Handles document summaries and interactions
 */
const DocumentManager = (() => {
    // Private properties
    let documentSummaries = {};
    
    /**
     * Load document summaries from API
     */
    const loadDocumentSummaries = async () => {
      try {
        // Get document list container and add loading state
        const documentList = UI.getElement('#document-list');
        documentList.innerHTML = '';
        documentList.appendChild(UI.createLoadingPlaceholder());
        
        // Get the current active knowledge base from KnowledgeManager
        const activeKB = KnowledgeManager.getActiveKnowledgeBase();
        
        // Get document summaries from API for the active knowledge base
        const data = await ApiService.getDocumentSummaries(activeKB);
        
        // Save document summaries
        documentSummaries = data || {};
        
        // Clear container
        documentList.innerHTML = '';
        
        // Add document items
        const documentNames = Object.keys(documentSummaries).sort();
        
        if (documentNames.length === 0) {
          documentList.appendChild(UI.createEmptyState('No document summaries available.'));
          return;
        }
        
        documentNames.forEach(docName => {
          const docInfo = documentSummaries[docName];
          const docElement = document.createElement('div');
          docElement.className = 'document-item';
          docElement.setAttribute('data-name', docName);
          
          // Check summary type for icon
          const summaryType = docInfo.summary_type || 'FULL';
          const iconClass = summaryType === 'FULL' ? 'text-green-500' : 'text-yellow-500';
          const iconSymbol = summaryType === 'FULL' ? '✓' : '⚠';
          
          docElement.innerHTML = `
            <div class="flex items-center">
              <span class="${iconClass} mr-2">${iconSymbol}</span>
              <div class="flex-1">
                <div class="document-item-title">${docName}</div>
                <div class="document-item-date">
                  ${new Date(docInfo.summarised_date).toLocaleDateString()}
                </div>
              </div>
            </div>
          `;
          
          // Add click event to show document summary
          docElement.addEventListener('click', () => {
            showDocumentSummary(docName);
          });
          
          documentList.appendChild(docElement);
        });
        
        // Apply search filter if exists
        const searchTerm = UI.getElement('#doc-search').value;
        if (searchTerm) {
          filterDocuments();
        }
      } catch (error) {
        console.error('Failed to load document summaries:', error);
        UI.showNotification('Failed to load document summaries');
        
        const documentList = UI.getElement('#document-list');
        documentList.innerHTML = '';
        
        const errorElement = document.createElement('div');
        errorElement.className = 'p-3 bg-red-100 text-red-800 rounded-lg mt-2';
        errorElement.textContent = `Error: ${error.message}`;
        documentList.appendChild(errorElement);
      }
    };
    
    /**
     * Show document summary in modal
     * @param {string} docName - Document name
     */
    const showDocumentSummary = (docName) => {
      const docInfo = documentSummaries[docName];
      
      if (!docInfo || !docInfo.summary) {
        UI.showNotification('No summary available for this document');
        return;
      }
      
      ModalManager.showDocumentSummary(docName, docInfo.summary);
    };
    
    /**
     * Filter documents by search term
     */
    const filterDocuments = () => {
      const searchTerm = UI.getElement('#doc-search').value.toLowerCase();
      const documentElements = UI.getAllElements('#document-list .document-item');

      documentElements.forEach(element => {
        const docName = element.getAttribute('data-name').toLowerCase();
        if (docName.includes(searchTerm)) {
          element.classList.remove('hidden');
        } else {
          element.classList.add('hidden');
        }
      });
    };

    /**
     * Show the generate summaries confirmation modal
     */
    const showGenerateSummariesModal = () => {
      const modal = UI.getElement('#generate-summaries-modal');
      const kbNameSpan = UI.getElement('#generate-kb-name');

      if (!modal) {
        console.error('Generate summaries modal not found');
        return;
      }

      // Get current knowledge base and its display name
      const activeKB = KnowledgeManager.getActiveKnowledgeBase();
      const availableKBs = KnowledgeManager.getAvailableKnowledgeBases();
      const kbInfo = availableKBs && availableKBs[activeKB];
      const kbName = kbInfo ? kbInfo.name : activeKB;

      if (kbNameSpan) {
        kbNameSpan.textContent = kbName;
      }

      modal.classList.add('show');
    };

    /**
     * Hide the generate summaries modal
     */
    const hideGenerateSummariesModal = () => {
      const modal = UI.getElement('#generate-summaries-modal');
      if (modal) {
        modal.classList.remove('show');
      }
    };

    // Track polling state
    let summaryPollingInterval = null;
    let initialSummaryCount = 0;

    /**
     * Start polling for job status and new summaries
     */
    const startPollingForSummaries = (collection) => {
      // Store initial count
      initialSummaryCount = Object.keys(documentSummaries).length;
      let pollCount = 0;
      const maxPolls = 60; // Poll for up to 5 minutes (60 * 5 seconds)

      console.log(`[Summary] Starting poll, initial count: ${initialSummaryCount}`);

      // Update button to show polling state
      const generateBtn = UI.getElement('#generate-summaries-btn');
      if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="animate-pulse">Generating...</span>';
      }

      summaryPollingInterval = setInterval(async () => {
        pollCount++;
        console.log(`[Summary] Poll ${pollCount}/${maxPolls}`);

        try {
          // First check job status
          const statusResponse = await fetch(`/api/generate_summaries/status/${collection}`);
          const status = await statusResponse.json();

          console.log(`[Summary] Job status: ${status.status}`);

          // If job completed, check for new summaries and stop polling
          if (status.status === 'completed' || status.status === 'error') {
            // Fetch current summaries one more time
            const data = await ApiService.getDocumentSummaries(collection);
            const currentCount = Object.keys(data || {}).length;
            const newCount = currentCount - initialSummaryCount;

            if (newCount > 0) {
              UI.showNotification(`${newCount} new summary(ies) generated!`);
              documentSummaries = data;
              loadDocumentSummaries();
            } else {
              UI.showNotification('Summary generation complete. No new summaries needed.');
            }

            stopPollingForSummaries();
            return;
          }

          // Job still running - check for new summaries
          const data = await ApiService.getDocumentSummaries(collection);
          const currentCount = Object.keys(data || {}).length;

          if (currentCount > initialSummaryCount) {
            const newCount = currentCount - initialSummaryCount;
            console.log(`[Summary] New summaries detected: ${newCount}`);
            UI.showNotification(`${newCount} new summary(ies) generated so far...`);

            // Update the document list
            documentSummaries = data;
            loadDocumentSummaries();

            // Update initial count for continued polling
            initialSummaryCount = currentCount;
          }

          // Stop polling after max attempts
          if (pollCount >= maxPolls) {
            stopPollingForSummaries();
            UI.showNotification('Summary generation monitoring stopped. Refresh to see updates.');
          }
        } catch (error) {
          console.error('[Summary] Polling error:', error);
        }
      }, 3000); // Poll every 3 seconds
    };

    /**
     * Stop polling for summaries
     */
    const stopPollingForSummaries = () => {
      if (summaryPollingInterval) {
        clearInterval(summaryPollingInterval);
        summaryPollingInterval = null;
      }

      // Reset button state
      const generateBtn = UI.getElement('#generate-summaries-btn');
      if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.innerHTML = 'Generate Summaries';
      }
    };

    /**
     * Start the summary generation process
     */
    const startSummaryGeneration = async () => {
      const activeKB = KnowledgeManager.getActiveKnowledgeBase();
      const generateBtn = UI.getElement('#confirm-generate-btn');

      // Disable button and show loading state
      if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Starting...';
      }

      try {
        const response = await fetch('/api/generate_summaries', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            collection: activeKB
          })
        });

        const data = await response.json();

        hideGenerateSummariesModal();

        if (data.error) {
          UI.showNotification('Error: ' + data.error);
        } else if (data.status === 'started') {
          UI.showNotification('Summary generation started. You will be notified of new summaries.');
          // Start polling for new summaries
          startPollingForSummaries(activeKB);
        } else {
          UI.showNotification(data.message || 'Summary generation complete');
          // Reload document summaries
          loadDocumentSummaries();
        }
      } catch (error) {
        console.error('Failed to start summary generation:', error);
        UI.showNotification('Failed to start: ' + error.message);
      } finally {
        // Reset modal button state
        if (generateBtn) {
          generateBtn.disabled = false;
          generateBtn.textContent = 'Start Generation';
        }
      }
    };

    /**
     * Initialize generate summaries modal events
     */
    const initGenerateSummariesModal = () => {
      const generateBtn = UI.getElement('#generate-summaries-btn');
      const closeBtn = UI.getElement('#close-generate-modal');
      const cancelBtn = UI.getElement('#cancel-generate-btn');
      const confirmBtn = UI.getElement('#confirm-generate-btn');
      const modal = UI.getElement('#generate-summaries-modal');

      if (generateBtn) {
        generateBtn.addEventListener('click', showGenerateSummariesModal);
      }

      if (closeBtn) {
        closeBtn.addEventListener('click', hideGenerateSummariesModal);
      }

      if (cancelBtn) {
        cancelBtn.addEventListener('click', hideGenerateSummariesModal);
      }

      if (confirmBtn) {
        confirmBtn.addEventListener('click', startSummaryGeneration);
      }

      // Close on click outside
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) {
            hideGenerateSummariesModal();
          }
        });
      }
    };

    // Public methods
    return {
      /**
       * Initialize document manager
       */
      init: () => {
        // Add document search functionality
        UI.getElement('#doc-search').addEventListener('input', filterDocuments);

        // Initialize generate summaries modal
        initGenerateSummariesModal();
      },

      /**
       * Load document summaries
       */
      loadDocumentSummaries,

      /**
       * Show document summary
       * @param {string} docName - Document name
       */
      showDocumentSummary
    };
  })();