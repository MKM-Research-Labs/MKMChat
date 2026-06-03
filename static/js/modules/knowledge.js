/**
 * MKM Research Labs - Knowledge Base Management
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
 *
 * Handles knowledge base switching and display
 */
const KnowledgeManager = (() => {
    // Private properties
    let activeKnowledgeBase = null;
    let availableKnowledgeBases = null;
    
    /**
     * Load available knowledge bases from API
     */
    const loadAvailableKnowledgeBases = async () => {
      try {
        // Get knowledge base list container and add loading state
        const kbList = UI.getElement('#knowledge-bases-list');
        kbList.innerHTML = '';
        kbList.appendChild(UI.createLoadingPlaceholder());
        
        // Get knowledge bases from API
        const data = await ApiService.getKnowledgeBases();
        
        console.log('[KB] API response:', data);
        
        if (!data || data.error) {
          throw new Error(data?.error || 'Failed to load knowledge bases');
        }
        
        // Validate response structure
        if (!data.indices || typeof data.indices !== 'object') {
          console.error('[KB] Invalid response - missing indices:', data);
          throw new Error('Invalid API response: missing indices');
        }
        
        if (!data.active) {
          console.error('[KB] Invalid response - missing active:', data);
          throw new Error('Invalid API response: missing active');
        }
        
        // Store available knowledge bases
        availableKnowledgeBases = data.indices;
        
        // Update active knowledge base
        activeKnowledgeBase = data.active;
        
        // Get display name with fallback
        const activeInfo = data.indices[activeKnowledgeBase];
        const activeDisplayName = activeInfo?.name || activeKnowledgeBase || 'Unknown KB';
        
        console.log('[KB] Setting active KB:', {
          key: activeKnowledgeBase,
          displayName: activeDisplayName,
          info: activeInfo
        });
        
        UI.setActiveKnowledgeBase(activeDisplayName);
        
        // Clear container
        kbList.innerHTML = '';
        
        // Validate we have knowledge bases
        if (!data.indices || Object.keys(data.indices).length === 0) {
          kbList.appendChild(UI.createEmptyState('No knowledge bases configured on server.'));
          return;
        }
        
        // Add knowledge base items
        Object.entries(data.indices).forEach(([key, info]) => {
          const isActive = key === activeKnowledgeBase;
          
          const kbElement = document.createElement('div');
          kbElement.className = `kb-item ${isActive ? 'kb-item-active' : ''}`;
          
          kbElement.innerHTML = `
            <div class="flex items-center">
              <div class="flex-1">
                <div class="kb-item-name">${info.name}</div>
                <div class="kb-item-key">${key}</div>
              </div>
              ${isActive ? '<div class="kb-item-active-badge">✓ Active</div>' : ''}
            </div>
          `;
          
          // Add click event to switch knowledge base
          if (!isActive) {
            kbElement.addEventListener('click', () => {
              switchKnowledgeBase(key);
            });
          }
          
          kbList.appendChild(kbElement);
        });
      } catch (error) {
        console.error('Failed to load knowledge bases:', error);
        
        const kbList = UI.getElement('#knowledge-bases-list');
        kbList.innerHTML = '';
        
        const errorElement = document.createElement('div');
        errorElement.className = 'p-3 bg-red-100 text-red-800 rounded-lg mt-2';
        errorElement.innerHTML = `
          <div class="font-semibold mb-2">Error Loading Knowledge Bases</div>
          <div class="text-sm">${error.message}</div>
          <div class="text-xs mt-2">The server may be unavailable or the API endpoint is not responding correctly.</div>
        `;
        kbList.appendChild(errorElement);
        
        // Set a default error state
        UI.setActiveKnowledgeBase('Error - Cannot Load');
      }
    };
    
    /**
     * Switch to a different knowledge base
     * @param {string} indexKey - Knowledge base key to switch to
     */
    const switchKnowledgeBase = async (indexKey) => {
      try {
        // Get display name from cached data
        let displayName = indexKey;
        if (availableKnowledgeBases && availableKnowledgeBases[indexKey]) {
          displayName = availableKnowledgeBases[indexKey].name;
        }

        // Create and display warning modal
        const modalId = 'kb-warning-modal';
        const warningModal = document.createElement('div');
        warningModal.className = 'modal show';
        warningModal.id = modalId;
        
        warningModal.innerHTML = `
          <div class="modal-content" style="max-width: 30rem;">
            <div class="modal-header">
              <h3 class="text-lg font-bold">Switching Knowledge Base</h3>
              <button class="close-btn" data-modal-id="${modalId}">&times;</button>
            </div>
            <div class="modal-body">
              <p class="mb-4">Switching to <strong>${displayName}</strong>. This may take a moment as the new index loads.</p>
              <div class="flex justify-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
              <div id="kb-status" class="mt-3 text-sm text-blue-600"></div>
            </div>
          </div>
        `;
        
        document.body.appendChild(warningModal);
        
        // Add close button functionality
        warningModal.querySelector('.close-btn').addEventListener('click', () => {
          warningModal.remove();
        });
        
        // Disable knowledge base items while switching
        const kbItems = UI.getAllElements('.kb-item');
        kbItems.forEach(item => {
          item.classList.add('opacity-50', 'pointer-events-none');
        });
        
        // Status updates
        const kbStatus = warningModal.querySelector('#kb-status');
        const updateStatus = (message) => {
          if (kbStatus) kbStatus.textContent = message;
          console.log(message);
        };
        
        updateStatus("Sending request to server...");
        
        const startTime = Date.now();
        
        // Call server API to switch index
        const data = await ApiService.switchKnowledgeBase(indexKey);
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        const loadTime = ((Date.now() - startTime) / 1000).toFixed(1);
        updateStatus(`Index loaded in ${loadTime} seconds`);
        
        // Add slight delay to show the success message
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Update the active knowledge base
        activeKnowledgeBase = data.active;
        
        // Show success notification
        UI.showNotification(data.message);
        
        // Update the KB indicator in the header
        const activeDisplayName = data.name || displayName;
        UI.setActiveKnowledgeBase(activeDisplayName);
        
        // Remove the warning modal
        setTimeout(() => {
          warningModal.remove();
        }, 500);
        
        // Reload the knowledge base list
        setTimeout(() => loadAvailableKnowledgeBases(), 500);
        
        // Reload document summaries for the new knowledge base
        setTimeout(() => {
          if (typeof DocumentManager !== 'undefined' && DocumentManager.loadDocumentSummaries) {
            DocumentManager.loadDocumentSummaries();
          }
        }, 600);
        
      } catch (error) {
        console.error('Failed to switch knowledge base:', error);
        
        // Show error in modal if it still exists
        const kbStatus = document.querySelector('#kb-status');
        if (kbStatus) {
          kbStatus.className = 'mt-3 text-sm text-red-600';
          kbStatus.textContent = `Error: ${error.message}`;
        }
        
        UI.showNotification(`Error switching knowledge base: ${error.message}`);
        
        // Re-enable knowledge base items
        const kbItems = UI.getAllElements('.kb-item');
        kbItems.forEach(item => {
          item.classList.remove('opacity-50', 'pointer-events-none');
        });
        
        // Remove modal after showing error
        setTimeout(() => {
          const modal = document.getElementById('kb-warning-modal');
          if (modal) modal.remove();
        }, 3000);
      }
    };
    
    // Public methods
    return {
      /**
       * Initialize knowledge manager
       */
      init: () => {
        // Initial load of knowledge base info
        loadAvailableKnowledgeBases();
      },
      
      /**
       * Get the currently active knowledge base key
       * @returns {string} - Current knowledge base key
       */
      getActiveKnowledgeBase: () => {
        return activeKnowledgeBase;
      },
      
      /**
       * Get all available knowledge bases
       * @returns {Object} - Available knowledge bases object
       */
      getAvailableKnowledgeBases: () => {
        return availableKnowledgeBases;
      },
      
      /**
       * Load available knowledge bases
       */
      loadAvailableKnowledgeBases,
      
      /**
       * Switch to a different knowledge base
       * @param {string} indexKey - Knowledge base key
       */
      switchKnowledgeBase
    };
  })();