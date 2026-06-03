/**
 * UI Module Tests
 */

const { loadModule } = require('./helpers/loadModule');

// Mock DOM before loading module
document.body.innerHTML = `
  <div id="notification"></div>
  <div id="sidebar" class="w-64"></div>
  <button id="toggle-sidebar"></button>
  <div class="tab-btn" id="tab1" data-panel="panel1"></div>
  <div class="tab-btn" id="tab2" data-panel="panel2"></div>
  <div class="panel-container" id="panel1"></div>
  <div class="panel-container" id="panel2" class="hidden"></div>
  <div id="active-kb-indicator"></div>
  <div id="summary-modal"></div>
  <div id="test-container"></div>
`;

const UI = loadModule('static/js/ui.js', 'UI');

describe('UI', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    // Reset DOM state
    document.getElementById('notification').classList.remove('show');
    document.getElementById('sidebar').className = 'w-64';
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('showNotification', () => {
    test('should show notification with message', () => {
      UI.showNotification('Test message');

      const notification = document.getElementById('notification');
      expect(notification.textContent).toBe('Test message');
      expect(notification.classList.contains('show')).toBe(true);
    });

    test('should hide notification after duration', () => {
      UI.showNotification('Test message', 1000);

      const notification = document.getElementById('notification');
      expect(notification.classList.contains('show')).toBe(true);

      jest.advanceTimersByTime(1000);
      expect(notification.classList.contains('show')).toBe(false);
    });
  });

  describe('toggleSidebar', () => {
    test('should collapse sidebar when expanded', () => {
      const sidebar = document.getElementById('sidebar');
      sidebar.className = 'w-64';

      UI.toggleSidebar();

      expect(sidebar.classList.contains('w-0')).toBe(true);
      expect(sidebar.classList.contains('w-64')).toBe(false);
    });

    test('should expand sidebar when collapsed', () => {
      const sidebar = document.getElementById('sidebar');
      sidebar.className = 'w-0';

      UI.toggleSidebar();

      expect(sidebar.classList.contains('w-64')).toBe(true);
      expect(sidebar.classList.contains('w-0')).toBe(false);
    });
  });

  describe('createLoadingPlaceholder', () => {
    test('should create element with loading-placeholder class', () => {
      const placeholder = UI.createLoadingPlaceholder();

      expect(placeholder.tagName).toBe('DIV');
      expect(placeholder.className).toBe('loading-placeholder');
    });
  });

  describe('createEmptyState', () => {
    test('should create element with message', () => {
      const emptyState = UI.createEmptyState('No items found');

      expect(emptyState.textContent).toBe('No items found');
      expect(emptyState.className).toContain('text-center');
    });
  });

  describe('setActiveKnowledgeBase', () => {
    test('should update indicator text', () => {
      UI.setActiveKnowledgeBase('Test KB');

      const indicator = document.getElementById('active-kb-indicator');
      expect(indicator.textContent).toBe('Test KB');
    });

    test('should show default text when name is null', () => {
      UI.setActiveKnowledgeBase(null);

      const indicator = document.getElementById('active-kb-indicator');
      expect(indicator.textContent).toBe('No KB Selected');
    });
  });

  describe('showModal', () => {
    test('should add show class to modal', () => {
      UI.showModal('summary-modal');

      const modal = document.getElementById('summary-modal');
      expect(modal.classList.contains('show')).toBe(true);
    });
  });

  describe('hideModal', () => {
    test('should remove show class from modal', () => {
      const modal = document.getElementById('summary-modal');
      modal.classList.add('show');

      UI.hideModal('summary-modal');

      expect(modal.classList.contains('show')).toBe(false);
    });
  });

  describe('clearContainer', () => {
    test('should clear container innerHTML', () => {
      const container = document.getElementById('test-container');
      container.innerHTML = '<p>Test content</p>';

      UI.clearContainer('test-container');

      expect(container.innerHTML).toBe('');
    });
  });

  describe('getElement', () => {
    test('should return element by selector', () => {
      const element = UI.getElement('#notification');
      expect(element).toBe(document.getElementById('notification'));
    });
  });

  describe('getAllElements', () => {
    test('should return all matching elements', () => {
      const elements = UI.getAllElements('.tab-btn');
      expect(elements.length).toBe(2);
    });
  });
});
