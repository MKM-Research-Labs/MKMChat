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
 * DocumentManager Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock dependencies
global.UI = {
  getElement: jest.fn(selector => document.querySelector(selector)),
  getAllElements: jest.fn(selector => document.querySelectorAll(selector)),
  showNotification: jest.fn(),
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
  getDocumentSummaries: jest.fn(() => Promise.resolve({
    'doc1.pdf': {
      summary: 'Summary of doc1',
      summarised_date: new Date().toISOString(),
      summary_type: 'FULL'
    },
    'doc2.pdf': {
      summary: 'Summary of doc2',
      summarised_date: new Date().toISOString(),
      summary_type: 'PARTIAL'
    }
  }))
};

global.KnowledgeManager = {
  getActiveKnowledgeBase: jest.fn(() => 'test_kb')
};

global.ModalManager = {
  showDocumentSummary: jest.fn()
};

// Mock DOM
document.body.innerHTML = `
  <div id="document-list"></div>
  <input id="doc-search" type="text" />
`;

const DocumentManager = loadModule('static/js/modules/documents.js', 'DocumentManager');

describe('DocumentManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    document.getElementById('document-list').innerHTML = '';
  });

  describe('init', () => {
    test('should initialize without errors', () => {
      expect(() => DocumentManager.init()).not.toThrow();
    });
  });

  describe('loadDocumentSummaries', () => {
    test('should fetch and display document summaries', async () => {
      await DocumentManager.loadDocumentSummaries();

      expect(ApiService.getDocumentSummaries).toHaveBeenCalled();

      const documentList = document.getElementById('document-list');
      expect(documentList.children.length).toBe(2);
    });

    test('should use active knowledge base', async () => {
      await DocumentManager.loadDocumentSummaries();

      expect(KnowledgeManager.getActiveKnowledgeBase).toHaveBeenCalled();
      expect(ApiService.getDocumentSummaries).toHaveBeenCalledWith('test_kb');
    });

    test('should show empty state when no documents', async () => {
      ApiService.getDocumentSummaries.mockResolvedValueOnce({});

      await DocumentManager.loadDocumentSummaries();

      expect(UI.createEmptyState).toHaveBeenCalled();
    });

    test('should handle API errors', async () => {
      ApiService.getDocumentSummaries.mockRejectedValueOnce(new Error('API Error'));

      await DocumentManager.loadDocumentSummaries();

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('Failed')
      );
    });
  });

  describe('showDocumentSummary', () => {
    test('should open modal with document summary', async () => {
      await DocumentManager.loadDocumentSummaries();

      DocumentManager.showDocumentSummary('doc1.pdf');

      expect(ModalManager.showDocumentSummary).toHaveBeenCalledWith(
        'doc1.pdf',
        'Summary of doc1'
      );
    });

    test('should show notification for missing summary', async () => {
      await DocumentManager.loadDocumentSummaries();

      DocumentManager.showDocumentSummary('nonexistent.pdf');

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('No summary')
      );
    });
  });
});
