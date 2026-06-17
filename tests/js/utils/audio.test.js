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
 * AudioUtils Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock localStorage for StorageUtils dependency
const localStorageMock = {
  getItem: jest.fn(() => '"UK English Female"'),
  setItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Mock UI
global.UI = {
  showNotification: jest.fn()
};

// Mock StorageUtils
global.StorageUtils = {
  getPreferredVoice: jest.fn(() => 'UK English Female'),
  savePreferredVoice: jest.fn()
};

// Mock responsiveVoice
global.responsiveVoice = {
  speak: jest.fn(),
  cancel: jest.fn(),
  pause: jest.fn(),
  resume: jest.fn(),
  isPlaying: jest.fn(() => false)
};

// Mock DOM
document.body.innerHTML = `
  <select id="voice-select">
    <option value="UK English Female">UK English Female</option>
    <option value="US English Male">US English Male</option>
  </select>
  <select id="chat-voice-select">
    <option value="UK English Female">UK English Female</option>
    <option value="US English Male">US English Male</option>
  </select>
`;

const AudioUtils = loadModule('static/js/utils/audio.js', 'AudioUtils');

describe('AudioUtils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.responsiveVoice.isPlaying.mockReturnValue(false);
  });

  describe('initVoicePreferences', () => {
    test('should set voice select values from storage', () => {
      AudioUtils.initVoicePreferences();

      expect(StorageUtils.getPreferredVoice).toHaveBeenCalled();
    });
  });

  describe('stopSpeaking', () => {
    test('should cancel speech when playing', () => {
      global.responsiveVoice.isPlaying.mockReturnValue(true);

      AudioUtils.stopSpeaking();

      expect(global.responsiveVoice.cancel).toHaveBeenCalled();
    });

    test('should not cancel when not playing', () => {
      global.responsiveVoice.isPlaying.mockReturnValue(false);

      AudioUtils.stopSpeaking();

      expect(global.responsiveVoice.cancel).not.toHaveBeenCalled();
    });
  });

  describe('formatChatForSpeech', () => {
    test('should format messages for speech', () => {
      const messages = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there' }
      ];

      const result = AudioUtils.formatChatForSpeech(messages);

      expect(result).toContain('User: Hello');
      expect(result).toContain('Assistant: Hi there');
    });

    test('should skip sources and error messages', () => {
      const messages = [
        { role: 'user', content: 'Hello' },
        { role: 'sources', content: 'Sources: file.pdf' },
        { role: 'error', content: 'Error occurred' }
      ];

      const result = AudioUtils.formatChatForSpeech(messages);

      expect(result).toContain('User: Hello');
      expect(result).not.toContain('Sources');
      expect(result).not.toContain('Error');
    });
  });
});
