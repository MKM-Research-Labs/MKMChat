/**
 * MKM Research Labs - Chat History
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 *
 * This software is provided under license by MKM Research Labs.
 * Use, reproduction, distribution, or modification of this code is subject to the
 * terms and conditions of the license agreement provided with this software.
 *
 * Handles chat history loading, saving, filtering, and persistence
 */
const ChatHistory = (() => {
  // Private properties
  let autoSaveTimeout = null;

  /**
   * Auto-save chat history with proper debouncing
   * @param {Array} chatMessages - Chat messages to save
   * @param {Function} onSaveComplete - Callback after successful save
   */
  const autoSaveChat = (chatMessages, onSaveComplete) => {
    if (chatMessages.length === 0) return;

    // Clear existing timeout to debounce
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout);
      autoSaveTimeout = null;
    }

    autoSaveTimeout = setTimeout(async () => {
      try {
        await ApiService.saveChat(chatMessages);
        UI.showNotification('Chat saved successfully!');
        if (onSaveComplete) {
          onSaveComplete();
        }
      } catch (error) {
        console.error('Failed to save chat:', error);
        UI.showNotification('Failed to save chat: ' + error.message);
      } finally {
        autoSaveTimeout = null;
      }
    }, 1000);
  };

  /**
   * Load chat history list
   * @param {Function} onChatClick - Callback when chat is clicked (receives chat object)
   * @param {Function} onChatPreview - Callback for chat preview (receives chat object)
   */
  const loadChatHistory = async (onChatClick, onChatPreview) => {
    try {
      const chatList = UI.getElement('#chat-list');
      if (!chatList) {
        console.warn('Chat list element not found');
        return;
      }

      chatList.innerHTML = '';
      chatList.appendChild(UI.createLoadingPlaceholder());

      // Get chat history from API
      const data = await ApiService.getChats();

      // Clear container
      chatList.innerHTML = '';

      // Convert chats to array if needed and validate
      let chatsArray = [];

      if (data && data.chats) {
        if (Array.isArray(data.chats)) {
          chatsArray = data.chats;
        } else if (typeof data.chats === 'object') {
          chatsArray = Object.values(data.chats);
        }
      } else if (data && typeof data === 'object' && !Array.isArray(data)) {
        chatsArray = Object.values(data);
      }

      // Filter out invalid entries
      chatsArray = chatsArray.filter(chat =>
        chat &&
        typeof chat === 'object' &&
        chat.messages &&
        Array.isArray(chat.messages)
      );

      if (chatsArray.length > 0) {
        chatsArray.forEach(chat => {
          const date = new Date(chat.timestamp);
          const chatButton = document.createElement('button');
          chatButton.className = 'chat-item';

          // Extract first user message for preview
          let previewText = 'Empty chat';
          for (const message of chat.messages) {
            if (message && message.role === 'user' && message.content) {
              previewText = message.content;
              break;
            }
          }

          chatButton.innerHTML = `
            <div class="chat-item-title">${date.toLocaleDateString()}</div>
            <div class="chat-item-time">${date.toLocaleTimeString()}</div>
            <div class="chat-item-preview">${previewText}</div>
          `;

          // Add event listener for chat preview
          chatButton.addEventListener('click', (e) => {
            if (e.ctrlKey || e.metaKey) {
              // Ctrl/Cmd + click: Load chat directly
              if (onChatClick) {
                onChatClick(chat);
              }
            } else {
              // Regular click: Show preview
              if (onChatPreview) {
                onChatPreview(chat);
              }
            }
          });

          chatList.appendChild(chatButton);
        });
      } else {
        chatList.appendChild(UI.createEmptyState('No chat history yet. Start a new chat!'));
      }

      // Apply search filter if exists
      const chatSearch = UI.getElement('#chat-search');
      if (chatSearch && chatSearch.value) {
        filterChats();
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
      UI.showNotification('Failed to load chat history');

      const chatList = UI.getElement('#chat-list');
      if (chatList) {
        chatList.innerHTML = '';

        const errorElement = document.createElement('div');
        errorElement.className = 'p-3 bg-red-100 text-red-800 rounded-lg mt-2';
        errorElement.textContent = `Error: ${error.message}`;
        chatList.appendChild(errorElement);
      }
    }
  };

  /**
   * Filter chats by search term
   */
  const filterChats = () => {
    const chatSearch = UI.getElement('#chat-search');
    if (!chatSearch) return;

    const searchTerm = chatSearch.value.toLowerCase();
    const chatButtons = Array.from(UI.getAllElements('#chat-list .chat-item'));

    chatButtons.forEach(button => {
      const chatText = button.textContent.toLowerCase();
      if (chatText.includes(searchTerm)) {
        button.classList.remove('hidden');
      } else {
        button.classList.add('hidden');
      }
    });
  };

  /**
   * Clear auto-save timeout (for cleanup)
   */
  const clearAutoSave = () => {
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout);
      autoSaveTimeout = null;
    }
  };

  // Public API
  return {
    autoSaveChat,
    loadChatHistory,
    filterChats,
    clearAutoSave
  };
})();
