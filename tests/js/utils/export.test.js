/**
 * ExportUtils Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock UI
global.UI = {
  showNotification: jest.fn()
};

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve())
  }
});

// Mock jsPDF
global.window = {
  jspdf: {
    jsPDF: jest.fn(() => ({
      setFont: jest.fn(),
      setFontSize: jest.fn(),
      setTextColor: jest.fn(),
      text: jest.fn(),
      internal: {
        pageSize: {
          getWidth: () => 210,
          getHeight: () => 297
        }
      },
      splitTextToSize: jest.fn(text => [text]),
      addPage: jest.fn(),
      save: jest.fn()
    }))
  }
};

// Trigger DOMContentLoaded to initialize jsPDF
document.body.innerHTML = '';

const ExportUtils = loadModule('static/js/utils/export.js', 'ExportUtils');

describe('ExportUtils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    navigator.clipboard.writeText.mockResolvedValue();
  });

  describe('formatChatForCopy', () => {
    test('should format messages with role headers', () => {
      const messages = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there' }
      ];

      const result = ExportUtils.formatChatForCopy(messages);

      expect(result).toContain('User:');
      expect(result).toContain('Hello');
      expect(result).toContain('Assistant:');
      expect(result).toContain('Hi there');
    });

    test('should include sources content', () => {
      const messages = [
        { role: 'assistant', content: 'Response' },
        { role: 'sources', content: 'Sources:\nfile.pdf (p.1)' }
      ];

      const result = ExportUtils.formatChatForCopy(messages);

      expect(result).toContain('Sources:');
      expect(result).toContain('file.pdf');
    });

    test('should not repeat role header for consecutive same-role messages', () => {
      const messages = [
        { role: 'user', content: 'First question' },
        { role: 'user', content: 'Another question' }
      ];

      const result = ExportUtils.formatChatForCopy(messages);

      // Should have User: only once since roles are the same
      const userCount = (result.match(/User:/g) || []).length;
      expect(userCount).toBe(1);
    });
  });

  describe('copyToClipboard', () => {
    test('should copy text to clipboard', async () => {
      const result = await ExportUtils.copyToClipboard('Test text');

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test text');
      expect(result).toBe(true);
      expect(UI.showNotification).toHaveBeenCalledWith('Copied to clipboard!');
    });

    test('should handle clipboard errors', async () => {
      navigator.clipboard.writeText.mockRejectedValueOnce(new Error('Failed'));

      const result = await ExportUtils.copyToClipboard('Test text');

      expect(result).toBe(false);
      expect(UI.showNotification).toHaveBeenCalledWith('Failed to copy text');
    });
  });
});
