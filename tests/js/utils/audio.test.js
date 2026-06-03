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
