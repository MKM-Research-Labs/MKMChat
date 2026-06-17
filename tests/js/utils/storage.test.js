/*
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
 */

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
