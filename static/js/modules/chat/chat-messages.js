/**
 * MKM Research Labs - Chat Messages
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 *
 * This software is provided under license by MKM Research Labs.
 * Use, reproduction, distribution, or modification of this code is subject to the
 * terms and conditions of the license agreement provided with this software.
 *
 * Handles message creation, rendering, sources display, and clipboard operations
 */
const ChatMessages = (() => {

  /**
   * Check if clipboard API is available
   * @returns {boolean}
   */
  const isClipboardAvailable = () => {
    return navigator.clipboard && typeof navigator.clipboard.writeText === 'function';
  };

  /**
   * Create a message element
   * @param {string} role - Message role (user, assistant, error)
   * @param {string} content - Message content
   * @param {number} messageIndex - Index in chatMessages array
   * @param {Function} onCopy - Callback for copy button click
   * @returns {HTMLElement} - Message element
   */
  const createMessageElement = (role, content, messageIndex, onCopy) => {
    const messageWrapper = document.createElement('div');
    messageWrapper.className = 'message-wrapper';

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'message-user' : role === 'error' ? 'message-error' : 'message-assistant'}`;

    // Format content with proper spacing
    if (role === 'assistant') {
      const formattedContent = content
        .replace(/\n\n+/g, '\n\n')
        .trim();

      messageDiv.textContent = formattedContent;
    } else {
      messageDiv.textContent = content;
    }

    // Add copy button only if clipboard API is available
    if (role === 'assistant' && isClipboardAvailable()) {
      const copyButton = document.createElement('button');
      copyButton.className = 'copy-message-btn';
      copyButton.textContent = 'Copy';
      copyButton.onclick = (e) => {
        e.preventDefault();
        if (onCopy) {
          onCopy(content, messageIndex);
        }
      };
      messageWrapper.appendChild(copyButton);
    }

    // Attach visualization if available
    if (role === 'assistant' && typeof VisualizationManager !== 'undefined') {
      VisualizationManager.attachVisualizationToMessage(messageWrapper, messageIndex, role);
    }

    messageWrapper.appendChild(messageDiv);
    return messageWrapper;
  };

  /**
   * Append a message to the chat container
   * @param {string} role - Message role
   * @param {string} content - Message content
   * @param {Array} chatMessages - Reference to chat messages array
   * @param {Function} onCopy - Callback for copy button click
   * @returns {Object} - The message object that was added
   */
  const appendMessage = (role, content, chatMessages, onCopy) => {
    const messageIndex = chatMessages.length;
    const messageElement = createMessageElement(role, content, messageIndex, onCopy);

    const chatContainer = UI.getElement('#chat-container');
    if (chatContainer) {
      chatContainer.appendChild(messageElement);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    const message = { role, content };
    chatMessages.push(message);
    return message;
  };

  /**
   * Append sources to the chat
   * @param {Array} sources - Sources array
   * @param {Array} chatMessages - Reference to chat messages array
   * @returns {Object} - The sources message object that was added
   */
  const appendSources = (sources, chatMessages) => {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'message-sources';

    // Clean and group sources by filename and collect page numbers
    const groupedSources = sources.reduce((acc, source) => {
      // Extract just the filename, removing any path
      const cleanFile = source.file.split('/').pop() || source.file;

      if (!acc[cleanFile]) {
        acc[cleanFile] = new Set();
      }
      acc[cleanFile].add(source.page);
      return acc;
    }, {});

    // Create the sources list
    let sourcesList = document.createElement('ul');
    sourcesList.className = 'list-disc pl-5 mt-1';

    sourcesDiv.innerHTML = 'Sources:';

    // Format sources list
    const formattedSources = Object.entries(groupedSources).map(([file, pages]) => {
      const pageNumbers = Array.from(pages).sort((a, b) => a - b);
      return `${file} (p.${pageNumbers.join(', ')})`;
    });

    // Add each source as a list item
    formattedSources.forEach(sourceText => {
      const listItem = document.createElement('li');
      listItem.className = 'mb-1';
      listItem.textContent = sourceText;
      sourcesList.appendChild(listItem);
    });

    sourcesDiv.appendChild(sourcesList);

    const chatContainer = UI.getElement('#chat-container');
    if (chatContainer) {
      chatContainer.appendChild(sourcesDiv);
    }

    // Save to chat history in the same list format
    const sourcesMessage = {
      role: 'sources',
      content: 'Sources:\n' + formattedSources.map(src => `• ${src}`).join('\n')
    };
    chatMessages.push(sourcesMessage);
    return sourcesMessage;
  };

  /**
   * Copy message with sources to clipboard
   * @param {string} text - Message text
   * @param {number} messageIndex - Message index
   * @param {Array} chatMessages - Reference to chat messages array
   */
  const copyMessageWithSources = async (text, messageIndex, chatMessages) => {
    if (!isClipboardAvailable()) {
      UI.showNotification('Clipboard not available');
      return;
    }

    try {
      // Find the next sources message after this message
      let sourcesText = '';
      for (let i = messageIndex + 1; i < chatMessages.length; i++) {
        if (chatMessages[i].role === 'sources') {
          sourcesText = '\n\n' + chatMessages[i].content;
          break;
        }
      }

      // Combine message content with sources
      const fullText = text + sourcesText;

      await ExportUtils.copyToClipboard(fullText);
    } catch (err) {
      UI.showNotification('Failed to copy text');
      console.error('Copy failed:', err);
    }
  };

  /**
   * Render a sources element for loaded chats
   * @param {string} content - Sources content
   * @returns {HTMLElement} - Sources div element
   */
  const createSourcesElement = (content) => {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'message-sources';
    sourcesDiv.innerHTML = content;
    return sourcesDiv;
  };

  // Public API
  return {
    isClipboardAvailable,
    createMessageElement,
    appendMessage,
    appendSources,
    copyMessageWithSources,
    createSourcesElement
  };
})();
