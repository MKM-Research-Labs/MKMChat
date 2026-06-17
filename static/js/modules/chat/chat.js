/**
 * MKM Research Labs - Chat Management
 * Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
 *
 * This software is licensed by MKM Research Labs for non-commercial 
 * research and educational use only. Any commercial use, including 
 * but not limited to use in or for products or services offered for sale, 
 * internal business operations intended for commercial advantage, or
 * research and development conducted for a commercial entity, is expressly
 * prohibited unless separately authorized in writing by MKM Research Labs.
 *
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
 * Main coordinator for chat messaging, history, and interactions
 *
 * Dependencies:
 * - ChatMessages (chat-messages.js)
 * - ChatHistory (chat-history.js)
 */
const ChatManager = (() => {
  // Private state
  let chatMessages = [];
  let currentChatId = null;

  /**
   * Get loading message - generic for all models
   * @returns {string} - Loading message
   */
  const getLoadingMessage = () => {
    return 'Processing your query...';
  };

  /**
   * Handle copy button click
   * @param {string} content - Message content
   * @param {number} messageIndex - Message index
   */
  const handleCopyClick = (content, messageIndex) => {
    ChatMessages.copyMessageWithSources(content, messageIndex, chatMessages);
  };

  /**
   * Trigger auto-save and reload history
   */
  const triggerAutoSave = () => {
    ChatHistory.autoSaveChat(chatMessages, () => {
      reloadChatHistory();
    });
  };

  /**
   * Reload chat history with proper callbacks
   */
  const reloadChatHistory = () => {
    ChatHistory.loadChatHistory(
      loadChat,
      (chat) => {
        if (typeof ModalManager !== 'undefined') {
          ModalManager.showChatPreview(chat);
        }
      }
    );
  };

  /**
   * Initialize chat form submission
   */
  const initChatForm = () => {
    const form = UI.getElement('#query-form');
    const input = UI.getElement('#query-input');
    const modelSelect = UI.getElement('#model-select');
    const chatContainer = UI.getElement('#chat-container');
    const newChatButton = UI.getElement('#new-chat');

    // Validate required elements
    if (!form || !input || !modelSelect || !chatContainer) {
      console.error('Required chat form elements not found');
      return;
    }

    // Restore last used model
    const lastModel = StorageUtils.getLastModel();
    if (lastModel && modelSelect.querySelector(`option[value="${lastModel}"]`)) {
      modelSelect.value = lastModel;
    }

    // Save model selection
    modelSelect.addEventListener('change', () => {
      StorageUtils.saveLastModel(modelSelect.value);
    });

    // New chat button
    if (newChatButton) {
      newChatButton.addEventListener('click', () => {
        chatContainer.innerHTML = '';
        chatMessages = [];
        currentChatId = null;
        input.value = '';
        input.focus();
      });
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const query = input.value.trim();
      if (!query) return;

      ChatMessages.appendMessage('user', query, chatMessages, handleCopyClick);
      input.value = '';

      // Get the selected model
      const selectedModel = modelSelect.value;

      // Show loader
      if (typeof LoaderUtils !== 'undefined') {
        LoaderUtils.show(getLoadingMessage());
      }

      try {
        const response = await ApiService.sendQuery(query, selectedModel);

        // Hide loader after receiving response
        if (typeof LoaderUtils !== 'undefined') {
          LoaderUtils.hide();
        }

        if (response.error) {
          ChatMessages.appendMessage('error', response.error, chatMessages, handleCopyClick);
        } else {
          ChatMessages.appendMessage('assistant', response.response, chatMessages, handleCopyClick);

          if (response.sources && Array.isArray(response.sources) && response.sources.length > 0) {
            ChatMessages.appendSources(response.sources, chatMessages);
          }
        }

        // Auto-save after each interaction
        triggerAutoSave();
      } catch (error) {
        // Hide loader on error
        if (typeof LoaderUtils !== 'undefined') {
          LoaderUtils.hide();
        }

        console.error('Query error:', error);
        ChatMessages.appendMessage('error', 'Failed to get response: ' + error.message, chatMessages, handleCopyClick);
        triggerAutoSave();
      }
    });
  };

  /**
   * Load chat into main chat container
   * @param {Object} chat - Chat object with messages
   */
  const loadChat = (chat) => {
    if (!chat || !chat.messages) {
      console.error('Invalid chat object:', chat);
      UI.showNotification('Failed to load chat: Invalid data');
      return;
    }

    const chatContainer = UI.getElement('#chat-container');
    if (!chatContainer) {
      console.error('Chat container not found');
      return;
    }

    chatContainer.innerHTML = '';

    chatMessages = chat.messages;
    currentChatId = chat.id;

    chatMessages.forEach((message, index) => {
      if (!message) return; // Skip invalid messages

      if (message.role === 'sources') {
        const sourcesElement = ChatMessages.createSourcesElement(message.content);
        chatContainer.appendChild(sourcesElement);
      } else {
        const messageElement = ChatMessages.createMessageElement(
          message.role,
          message.content,
          index,
          handleCopyClick
        );
        chatContainer.appendChild(messageElement);
      }
    });

    chatContainer.scrollTop = chatContainer.scrollHeight;
  };

  // Public API
  return {
    /**
     * Initialize chat manager
     */
    init: () => {
      initChatForm();

      // Add chat search functionality
      const chatSearch = UI.getElement('#chat-search');
      if (chatSearch) {
        chatSearch.addEventListener('input', ChatHistory.filterChats);
      }

      // Initial load
      reloadChatHistory();
    },

    /**
     * Load chat into main chat container
     * @param {Object} chat - Chat object with messages
     */
    loadChat: loadChat,

    /**
     * Reload chat history
     */
    reloadChatHistory: reloadChatHistory,

    /**
     * Get current chat messages
     * @returns {Array} - Chat messages
     */
    getChatMessages: () => {
      return [...chatMessages];
    },

    /**
     * Clear auto-save timeout (for cleanup)
     */
    clearAutoSave: ChatHistory.clearAutoSave
  };
})();
