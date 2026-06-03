/**
 * KnowledgeManager Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock dependencies
global.UI = {
  getElement: jest.fn(selector => document.querySelector(selector)),
  getAllElements: jest.fn(selector => document.querySelectorAll(selector)),
  showNotification: jest.fn(),
  setActiveKnowledgeBase: jest.fn(),
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

global.ApiService = {
  getKnowledgeBases: jest.fn(() => Promise.resolve({
    indices: {
      'misc': { name: 'Miscellaneous' },
      'phys': { name: 'Physics' },
      'hist': { name: 'History' }
    },
    active: 'misc'
  })),
  switchKnowledgeBase: jest.fn(() => Promise.resolve({
    active: 'phys',
    name: 'Physics',
    message: 'Switched to Physics'
  }))
};

global.DocumentManager = {
  loadDocumentSummaries: jest.fn()
};

// Mock DOM
document.body.innerHTML = `
  <div id="knowledge-bases-list"></div>
`;

const KnowledgeManager = loadModule('static/js/modules/knowledge.js', 'KnowledgeManager');

describe('KnowledgeManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    document.getElementById('knowledge-bases-list').innerHTML = '';
  });

  afterEach(() => {
    jest.useRealTimers();
    // Clean up any modals
    const modal = document.getElementById('kb-warning-modal');
    if (modal) modal.remove();
  });

  describe('init', () => {
    test('should load knowledge bases on init', async () => {
      KnowledgeManager.init();

      // Wait for promises
      await Promise.resolve();

      expect(ApiService.getKnowledgeBases).toHaveBeenCalled();
    });
  });

  describe('loadAvailableKnowledgeBases', () => {
    test('should fetch and display knowledge bases', async () => {
      await KnowledgeManager.loadAvailableKnowledgeBases();

      expect(ApiService.getKnowledgeBases).toHaveBeenCalled();

      const kbList = document.getElementById('knowledge-bases-list');
      expect(kbList.children.length).toBe(3);
    });

    test('should set active knowledge base indicator', async () => {
      await KnowledgeManager.loadAvailableKnowledgeBases();

      expect(UI.setActiveKnowledgeBase).toHaveBeenCalledWith('Miscellaneous');
    });

    test('should handle API errors', async () => {
      ApiService.getKnowledgeBases.mockRejectedValueOnce(new Error('Network error'));

      await KnowledgeManager.loadAvailableKnowledgeBases();

      expect(UI.setActiveKnowledgeBase).toHaveBeenCalledWith('Error - Cannot Load');
    });

    test('should handle missing indices in response', async () => {
      ApiService.getKnowledgeBases.mockResolvedValueOnce({
        active: 'test'
      });

      await KnowledgeManager.loadAvailableKnowledgeBases();

      const kbList = document.getElementById('knowledge-bases-list');
      expect(kbList.textContent).toContain('Error');
    });
  });

  describe('getActiveKnowledgeBase', () => {
    test('should return active knowledge base key', async () => {
      await KnowledgeManager.loadAvailableKnowledgeBases();

      const active = KnowledgeManager.getActiveKnowledgeBase();

      expect(active).toBe('misc');
    });
  });

  describe('getAvailableKnowledgeBases', () => {
    test('should return all knowledge bases', async () => {
      await KnowledgeManager.loadAvailableKnowledgeBases();

      const available = KnowledgeManager.getAvailableKnowledgeBases();

      expect(available).toHaveProperty('misc');
      expect(available).toHaveProperty('phys');
      expect(available).toHaveProperty('hist');
    });
  });

  describe('switchKnowledgeBase', () => {
    test('should call API to switch knowledge base', async () => {
      await KnowledgeManager.loadAvailableKnowledgeBases();

      // Start the switch - run all timers and promises
      const switchPromise = KnowledgeManager.switchKnowledgeBase('phys');

      // Run all pending timers and promises
      await jest.runAllTimersAsync();

      expect(ApiService.switchKnowledgeBase).toHaveBeenCalledWith('phys');
    }, 10000);

    test('should show notification on success', async () => {
      await KnowledgeManager.loadAvailableKnowledgeBases();

      const switchPromise = KnowledgeManager.switchKnowledgeBase('phys');
      await jest.runAllTimersAsync();

      expect(UI.showNotification).toHaveBeenCalledWith('Switched to Physics');
    }, 10000);

    test('should update active KB indicator', async () => {
      await KnowledgeManager.loadAvailableKnowledgeBases();

      const switchPromise = KnowledgeManager.switchKnowledgeBase('phys');
      await jest.runAllTimersAsync();

      expect(UI.setActiveKnowledgeBase).toHaveBeenCalledWith('Physics');
    }, 10000);
  });
});
