/**
 * StorageUtils Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn(key => store[key] || null),
    setItem: jest.fn((key, value) => { store[key] = value; }),
    removeItem: jest.fn(key => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; })
  };
})();

Object.defineProperty(global, 'localStorage', { value: localStorageMock });

const StorageUtils = loadModule('static/js/utils/storage.js', 'StorageUtils');

describe('StorageUtils', () => {
  beforeEach(() => {
    localStorageMock.clear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  describe('savePreferredVoice', () => {
    test('should save voice to localStorage', () => {
      StorageUtils.savePreferredVoice('US English Male');

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'preferredVoice',
        '"US English Male"'
      );
    });
  });

  describe('getPreferredVoice', () => {
    test('should return saved voice', () => {
      localStorageMock.getItem.mockReturnValueOnce('"US English Male"');

      const voice = StorageUtils.getPreferredVoice();

      expect(voice).toBe('US English Male');
    });

    test('should return default voice when not set', () => {
      localStorageMock.getItem.mockReturnValueOnce(null);

      const voice = StorageUtils.getPreferredVoice();

      expect(voice).toBe('UK English Female');
    });
  });

  describe('saveLastModel', () => {
    test('should save model to localStorage', () => {
      StorageUtils.saveLastModel('gpt-4');

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'lastUsedModel',
        '"gpt-4"'
      );
    });
  });

  describe('getLastModel', () => {
    test('should return saved model', () => {
      localStorageMock.getItem.mockReturnValueOnce('"gpt-4"');

      const model = StorageUtils.getLastModel();

      expect(model).toBe('gpt-4');
    });

    test('should return default model when not set', () => {
      localStorageMock.getItem.mockReturnValueOnce(null);

      const model = StorageUtils.getLastModel();

      expect(model).toBe('claude-3.5-sonnet');
    });
  });
});
