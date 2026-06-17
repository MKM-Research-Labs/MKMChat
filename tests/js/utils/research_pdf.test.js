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
 * ResearchPDFGenerator Tests
 *
 * Note: These tests focus on the module's validation and error handling.
 * PDF generation requires jsPDF which is mocked here.
 */

const { loadModule } = require('../helpers/loadModule');

// Set up window.jspdf mock BEFORE loading the module
const mockPDF = {
  setFont: jest.fn(),
  setFontSize: jest.fn(),
  setTextColor: jest.fn(),
  setFillColor: jest.fn(),
  setDrawColor: jest.fn(),
  setLineWidth: jest.fn(),
  text: jest.fn(),
  rect: jest.fn(),
  roundedRect: jest.fn(),
  line: jest.fn(),
  addPage: jest.fn(),
  save: jest.fn(),
  internal: {
    pageSize: {
      getWidth: () => 210,
      getHeight: () => 297
    }
  },
  splitTextToSize: jest.fn(text => text ? [text] : [])
};

// Assign to global.window.jspdf directly
global.window = global.window || {};
global.window.jspdf = {
  jsPDF: jest.fn(() => mockPDF)
};

document.body.innerHTML = '';

const ResearchPDFGenerator = loadModule('static/js/utils/research_pdf.js', 'ResearchPDFGenerator');

describe('ResearchPDFGenerator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    ResearchPDFGenerator.clearCache();
  });

  const mockResult = {
    query: 'Test research query',
    model: 'gpt-4',
    timestamp: new Date().toISOString(),
    total_sources: 10,
    total_time_ms: 5000,
    synthesized_answer: 'This is the synthesized answer.',
    kb_results: [
      {
        kb_key: 'test_kb',
        kb_name: 'Test Knowledge Base',
        success: true,
        response: 'Test response from KB',
        doc_count: 5,
        query_time_ms: 1000,
        sources: [
          { file: 'doc1.pdf', page: 1 },
          { file: 'doc2.pdf', page: 5 }
        ]
      }
    ]
  };

  describe('generate', () => {
    test('should return null for null result', () => {
      const pdf = ResearchPDFGenerator.generate(null);
      expect(pdf).toBeNull();
    });

    test('should return null for undefined result', () => {
      const pdf = ResearchPDFGenerator.generate(undefined);
      expect(pdf).toBeNull();
    });

    test('should return null for result without kb_results', () => {
      const pdf = ResearchPDFGenerator.generate({ query: 'test' });
      expect(pdf).toBeNull();
    });

    test('should return null for result with empty kb_results', () => {
      const pdf = ResearchPDFGenerator.generate({ query: 'test', kb_results: null });
      expect(pdf).toBeNull();
    });
  });

  describe('generateAndDownload', () => {
    test('should return false for null result', () => {
      const result = ResearchPDFGenerator.generateAndDownload(null);
      expect(result).toBe(false);
    });

    test('should return false for invalid result', () => {
      const result = ResearchPDFGenerator.generateAndDownload({});
      expect(result).toBe(false);
    });
  });

  describe('getLastPDF', () => {
    test('should return null initially', () => {
      ResearchPDFGenerator.clearCache();
      expect(ResearchPDFGenerator.getLastPDF()).toBeNull();
    });
  });

  describe('downloadLast', () => {
    test('should return false when no PDF has been generated', () => {
      ResearchPDFGenerator.clearCache();
      const result = ResearchPDFGenerator.downloadLast();
      expect(result).toBe(false);
    });

    test('should return false with filename when no PDF generated', () => {
      ResearchPDFGenerator.clearCache();
      const result = ResearchPDFGenerator.downloadLast('test.pdf');
      expect(result).toBe(false);
    });
  });

  describe('clearCache', () => {
    test('should clear any cached PDF', () => {
      ResearchPDFGenerator.clearCache();
      expect(ResearchPDFGenerator.getLastPDF()).toBeNull();
    });

    test('should not throw when called multiple times', () => {
      expect(() => {
        ResearchPDFGenerator.clearCache();
        ResearchPDFGenerator.clearCache();
      }).not.toThrow();
    });
  });
});
