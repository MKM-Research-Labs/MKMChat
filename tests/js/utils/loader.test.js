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
