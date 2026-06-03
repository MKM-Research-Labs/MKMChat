/**
 * LoaderUtils Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock DOM
document.body.innerHTML = `
  <div id="chat-container"></div>
`;

const LoaderUtils = loadModule('static/js/utils/loader.js', 'LoaderUtils');

describe('LoaderUtils', () => {
  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = `<div id="chat-container"></div>`;
    LoaderUtils.init();
  });

  describe('init', () => {
    test('should create loader element', () => {
      const loader = document.getElementById('query-loader');
      expect(loader).not.toBeNull();
    });

    test('should have loader-container class', () => {
      const loader = document.getElementById('query-loader');
      expect(loader.classList.contains('loader-container')).toBe(true);
    });
  });

  describe('show', () => {
    test('should add active class to loader', () => {
      LoaderUtils.show();

      const loader = document.getElementById('query-loader');
      expect(loader.classList.contains('active')).toBe(true);
    });

    test('should update message when provided', () => {
      LoaderUtils.show('Custom loading message...');

      const loaderText = document.querySelector('.loader-text');
      expect(loaderText.textContent).toBe('Custom loading message...');
    });

    test('should add loading class to chat container', () => {
      LoaderUtils.show();

      const chatContainer = document.getElementById('chat-container');
      expect(chatContainer.classList.contains('chat-container-loading')).toBe(true);
    });
  });

  describe('hide', () => {
    test('should remove active class from loader', () => {
      LoaderUtils.show();
      LoaderUtils.hide();

      const loader = document.getElementById('query-loader');
      expect(loader.classList.contains('active')).toBe(false);
    });

    test('should remove loading class from chat container', () => {
      LoaderUtils.show();
      LoaderUtils.hide();

      const chatContainer = document.getElementById('chat-container');
      expect(chatContainer.classList.contains('chat-container-loading')).toBe(false);
    });
  });

  describe('isActive', () => {
    test('should return true when loader is visible', () => {
      LoaderUtils.show();
      expect(LoaderUtils.isActive()).toBe(true);
    });

    test('should return false when loader is hidden', () => {
      LoaderUtils.hide();
      expect(LoaderUtils.isActive()).toBe(false);
    });
  });
});
