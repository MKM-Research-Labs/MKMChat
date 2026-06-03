/**
 * ModalManager Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock dependencies
global.UI = {
  getElement: jest.fn(selector => document.querySelector(selector)),
  showModal: jest.fn(),
  hideModal: jest.fn(),
  showNotification: jest.fn()
};

global.ExportUtils = {
  copyToClipboard: jest.fn(() => Promise.resolve(true)),
  formatChatForCopy: jest.fn(msgs => msgs.map(m => m.content).join('\n')),
  exportChatToPDF: jest.fn(),
  exportDocumentToPDF: jest.fn()
};

global.ApiService = {
  deleteChat: jest.fn(() => Promise.resolve({ success: true }))
};

global.ChatManager = {
  loadChat: jest.fn(),
  reloadChatHistory: jest.fn()
};

// Mock responsiveVoice
global.responsiveVoice = {
  speak: jest.fn(),
  cancel: jest.fn(),
  isPlaying: jest.fn(() => false),
  voiceSupport: jest.fn(() => true)
};

// Mock DOM
document.body.innerHTML = `
  <div id="summary-modal">
    <button id="close-modal"></button>
    <h3 id="modal-title"></h3>
    <div id="modal-content"></div>
    <select id="voice-select">
      <option value="UK English Male">UK English Male</option>
    </select>
    <button id="listen-summary"><span id="listen-icon"></span></button>
    <button id="copy-summary"></button>
    <button id="export-summary-pdf"></button>
    <button id="use-summary"></button>
  </div>
  <div id="chat-preview-modal">
    <button id="close-chat-modal"></button>
    <h3 id="chat-modal-title"></h3>
    <div id="chat-modal-content"></div>
    <select id="chat-voice-select">
      <option value="UK English Male">UK English Male</option>
    </select>
    <button id="listen-chat"><span id="chat-listen-icon"></span></button>
    <button id="copy-chat"></button>
    <button id="export-chat-pdf"></button>
    <button id="load-chat"></button>
    <button id="delete-chat"></button>
  </div>
  <input id="query-input" type="text" />
`;

const ModalManager = loadModule('static/js/modules/modals.js', 'ModalManager');

describe('ModalManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    ModalManager.init();
  });

  describe('init', () => {
    test('should initialize without errors', () => {
      expect(() => ModalManager.init()).not.toThrow();
    });
  });

  describe('showDocumentSummary', () => {
    test('should set modal title and content', () => {
      ModalManager.showDocumentSummary('test.pdf', 'Test summary content');

      expect(document.getElementById('modal-title').textContent).toBe('test.pdf');
      expect(document.getElementById('modal-content').textContent).toBe('Test summary content');
    });

    test('should show the modal', () => {
      ModalManager.showDocumentSummary('test.pdf', 'Summary');

      expect(UI.showModal).toHaveBeenCalledWith('summary-modal');
    });
  });

  describe('showChatPreview', () => {
    test('should render chat messages in modal', () => {
      const chat = {
        timestamp: new Date().toISOString(),
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there' }
        ]
      };

      ModalManager.showChatPreview(chat);

      const content = document.getElementById('chat-modal-content');
      expect(content.innerHTML).toContain('User');
      expect(content.innerHTML).toContain('Hello');
    });

    test('should set title from first user message', () => {
      const chat = {
        timestamp: new Date().toISOString(),
        messages: [
          { role: 'user', content: 'Test question here' },
          { role: 'assistant', content: 'Answer' }
        ]
      };

      ModalManager.showChatPreview(chat);

      const title = document.getElementById('chat-modal-title');
      expect(title.textContent).toContain('Test question');
    });

    test('should show the chat preview modal', () => {
      const chat = {
        timestamp: new Date().toISOString(),
        messages: []
      };

      ModalManager.showChatPreview(chat);

      expect(UI.showModal).toHaveBeenCalledWith('chat-preview-modal');
    });

    test('should handle sources messages', () => {
      const chat = {
        timestamp: new Date().toISOString(),
        messages: [
          { role: 'assistant', content: 'Response' },
          { role: 'sources', content: 'Sources:\nfile.pdf' }
        ]
      };

      ModalManager.showChatPreview(chat);

      const content = document.getElementById('chat-modal-content');
      expect(content.innerHTML).toContain('Sources');
    });
  });

  describe('delete chat button', () => {
    beforeEach(() => {
      global.confirm = jest.fn(() => true);
    });

    test('should call ApiService.deleteChat when confirmed', async () => {
      const chat = {
        id: 'chat_to_delete',
        timestamp: new Date().toISOString(),
        messages: [{ role: 'user', content: 'Hello' }]
      };

      ModalManager.showChatPreview(chat);

      const deleteBtn = document.getElementById('delete-chat');
      deleteBtn.click();

      // Wait for async handler
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(global.confirm).toHaveBeenCalled();
      expect(ApiService.deleteChat).toHaveBeenCalledWith('chat_to_delete');
      expect(UI.hideModal).toHaveBeenCalledWith('chat-preview-modal');
      expect(ChatManager.reloadChatHistory).toHaveBeenCalled();
    });

    test('should not delete when user cancels confirmation', async () => {
      global.confirm = jest.fn(() => false);

      const chat = {
        id: 'chat_keep',
        timestamp: new Date().toISOString(),
        messages: [{ role: 'user', content: 'Keep me' }]
      };

      ModalManager.showChatPreview(chat);

      const deleteBtn = document.getElementById('delete-chat');
      deleteBtn.click();

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(global.confirm).toHaveBeenCalled();
      expect(ApiService.deleteChat).not.toHaveBeenCalled();
    });

    test('should show error notification on delete failure', async () => {
      ApiService.deleteChat.mockRejectedValueOnce(new Error('Server error'));

      const chat = {
        id: 'chat_fail',
        timestamp: new Date().toISOString(),
        messages: [{ role: 'user', content: 'Fail' }]
      };

      ModalManager.showChatPreview(chat);

      const deleteBtn = document.getElementById('delete-chat');
      deleteBtn.click();

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('Failed to delete')
      );
    });
  });

  describe('isVoiceAvailable', () => {
    test('should return true when responsiveVoice is available', () => {
      expect(ModalManager.isVoiceAvailable()).toBe(true);
    });

    test('should return false when responsiveVoice is not available', () => {
      global.responsiveVoice.voiceSupport.mockReturnValueOnce(false);
      expect(ModalManager.isVoiceAvailable()).toBe(false);
    });
  });
});
