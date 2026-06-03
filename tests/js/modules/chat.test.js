/**
 * ChatManager Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(() => '"claude-3.5-sonnet"'),
  setItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve())
  }
});

// Mock dependencies
global.UI = {
  getElement: jest.fn(selector => document.querySelector(selector)),
  getAllElements: jest.fn(selector => document.querySelectorAll(selector)),
  showNotification: jest.fn(),
  createLoadingPlaceholder: jest.fn(() => {
    const div = document.createElement('div');
    div.className = 'loading-placeholder';
    return div;
  }),
  createEmptyState: jest.fn(msg => {
    const div = document.createElement('div');
    div.textContent = msg;
    return div;
  })
};

global.StorageUtils = {
  getLastModel: jest.fn(() => 'claude-3.5-sonnet'),
  saveLastModel: jest.fn()
};

global.ApiService = {
  sendQuery: jest.fn(() => Promise.resolve({
    response: 'Test response',
    sources: []
  })),
  saveChat: jest.fn(() => Promise.resolve({ status: 'ok' })),
  getChats: jest.fn(() => Promise.resolve({ chats: [] }))
};

global.LoaderUtils = {
  show: jest.fn(),
  hide: jest.fn()
};

global.ExportUtils = {
  copyToClipboard: jest.fn(() => Promise.resolve(true))
};

global.VisualizationManager = undefined;
global.ModalManager = undefined;

// Mock DOM
document.body.innerHTML = `
  <form id="query-form">
    <input id="query-input" type="text" />
    <select id="model-select">
      <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
      <option value="gpt-4">GPT-4</option>
    </select>
    <button type="submit">Send</button>
  </form>
  <div id="chat-container"></div>
  <button id="new-chat">New Chat</button>
  <div id="chat-list"></div>
  <input id="chat-search" type="text" />
`;

// Load modules in dependency order
const ChatMessages = loadModule('static/js/modules/chat/chat-messages.js', 'ChatMessages');
global.ChatMessages = ChatMessages;
const ChatHistory = loadModule('static/js/modules/chat/chat-history.js', 'ChatHistory');
global.ChatHistory = ChatHistory;
const ChatManager = loadModule('static/js/modules/chat/chat.js', 'ChatManager');

describe('ChatManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    document.getElementById('chat-container').innerHTML = '';
    document.getElementById('chat-list').innerHTML = '';
    document.getElementById('query-input').value = '';
  });

  afterEach(() => {
    jest.useRealTimers();
    ChatManager.clearAutoSave();
  });

  describe('init', () => {
    test('should initialize without errors', () => {
      expect(() => ChatManager.init()).not.toThrow();
    });

    test('should load last used model', () => {
      ChatManager.init();
      expect(StorageUtils.getLastModel).toHaveBeenCalled();
    });
  });

  describe('getChatMessages', () => {
    test('should return empty array initially', () => {
      const messages = ChatManager.getChatMessages();
      expect(Array.isArray(messages)).toBe(true);
    });

    test('should return copy of messages array', () => {
      const messages1 = ChatManager.getChatMessages();
      const messages2 = ChatManager.getChatMessages();
      expect(messages1).not.toBe(messages2);
    });
  });

  describe('loadChat', () => {
    test('should load chat messages into container', () => {
      ChatManager.init();

      const chat = {
        id: 'test-id',
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there' }
        ]
      };

      ChatManager.loadChat(chat);

      const container = document.getElementById('chat-container');
      expect(container.children.length).toBeGreaterThan(0);
    });

    test('should handle invalid chat object', () => {
      ChatManager.init();

      expect(() => ChatManager.loadChat(null)).not.toThrow();
      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('Failed')
      );
    });

    test('should handle sources messages', () => {
      ChatManager.init();

      const chat = {
        id: 'test-id',
        messages: [
          { role: 'assistant', content: 'Response' },
          { role: 'sources', content: 'Sources:\nfile.pdf' }
        ]
      };

      ChatManager.loadChat(chat);

      const container = document.getElementById('chat-container');
      expect(container.innerHTML).toContain('source');
    });
  });

  describe('clearAutoSave', () => {
    test('should not throw when called', () => {
      expect(() => ChatManager.clearAutoSave()).not.toThrow();
    });
  });
});
