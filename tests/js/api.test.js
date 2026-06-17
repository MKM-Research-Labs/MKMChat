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
 * API Service Tests
 */

const { loadModule } = require('./helpers/loadModule');

// Load ApiService module
const ApiService = loadModule('static/js/api.js', 'ApiService');

describe('ApiService', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  describe('getEndpoints', () => {
    test('should return all endpoint definitions', () => {
      const endpoints = ApiService.getEndpoints();

      expect(endpoints).toHaveProperty('query');
      expect(endpoints).toHaveProperty('saveChat');
      expect(endpoints).toHaveProperty('getChats');
      expect(endpoints).toHaveProperty('researchQuery');
      expect(endpoints.query).toBe('/query');
    });
  });

  describe('sendQuery', () => {
    test('should send POST request with query and model', async () => {
      const mockResponse = { response: 'Test response', sources: [] };
      fetch.mockResolvedValueOnce(mockFetchResponse(mockResponse));

      const result = await ApiService.sendQuery('test query', 'gpt-4');

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith(
        '/query',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'test query', model: 'gpt-4' })
        })
      );
      expect(result).toEqual(mockResponse);
    });

    test('should throw error on server error', async () => {
      fetch.mockResolvedValueOnce(mockFetchResponse({ error: 'Server error' }, 500));

      await expect(ApiService.sendQuery('test', 'model'))
        .rejects.toThrow('Server error');
    });
  });

  describe('saveChat', () => {
    test('should send messages with timestamp', async () => {
      const messages = [{ role: 'user', content: 'Hello' }];
      fetch.mockResolvedValueOnce(mockFetchResponse({ status: 'saved' }));

      await ApiService.saveChat(messages);

      expect(fetch).toHaveBeenCalledWith(
        '/save_chat',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"messages"')
        })
      );
    });
  });

  describe('getChats', () => {
    test('should make GET request to get chats endpoint', async () => {
      const mockChats = [{ id: 1, messages: [] }];
      fetch.mockResolvedValueOnce(mockFetchResponse(mockChats));

      const result = await ApiService.getChats();

      expect(fetch).toHaveBeenCalledWith(
        '/get_chats',
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual(mockChats);
    });
  });

  describe('deleteChat', () => {
    test('should send DELETE request with chat ID', async () => {
      fetch.mockResolvedValueOnce(mockFetchResponse({ success: true }));

      const result = await ApiService.deleteChat('chat_123');

      expect(fetch).toHaveBeenCalledWith(
        '/delete_chat/chat_123',
        expect.objectContaining({ method: 'DELETE' })
      );
      expect(result).toEqual({ success: true });
    });

    test('should throw error when chat not found', async () => {
      fetch.mockResolvedValueOnce(mockFetchResponse({ error: 'Chat not found' }, 404));

      await expect(ApiService.deleteChat('nonexistent'))
        .rejects.toThrow('Chat not found');
    });
  });

  describe('getDocumentSummaries', () => {
    test('should make request without params when no knowledge base specified', async () => {
      fetch.mockResolvedValueOnce(mockFetchResponse([]));

      await ApiService.getDocumentSummaries();

      expect(fetch).toHaveBeenCalledWith(
        '/get_summarised_files',
        expect.any(Object)
      );
    });

    test('should include docs_type param when knowledge base specified', async () => {
      fetch.mockResolvedValueOnce(mockFetchResponse([]));

      await ApiService.getDocumentSummaries('phys');

      expect(fetch).toHaveBeenCalledWith(
        '/get_summarised_files?docs_type=phys',
        expect.any(Object)
      );
    });
  });

  describe('getResearchStreamUrl', () => {
    test('should build correct URL with query and model', () => {
      const url = ApiService.getResearchStreamUrl('research question', 'gpt-4');

      expect(url).toContain('/research_query_stream');
      expect(url).toContain('query=research%20question');
      expect(url).toContain('model=gpt-4');
    });

    test('should include kb_keys when provided', () => {
      const url = ApiService.getResearchStreamUrl('question', 'model', ['phys', 'misc']);

      expect(url).toContain('kb_keys=phys%2Cmisc');
    });
  });

  describe('isResearchAvailable', () => {
    test('should return true when endpoint exists', async () => {
      fetch.mockResolvedValueOnce({ status: 200 });

      const result = await ApiService.isResearchAvailable();

      expect(result).toBe(true);
    });

    test('should return false when endpoint returns 404', async () => {
      fetch.mockResolvedValueOnce({ status: 404 });

      const result = await ApiService.isResearchAvailable();

      expect(result).toBe(false);
    });

    test('should return false on network error', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await ApiService.isResearchAvailable();

      expect(result).toBe(false);
    });
  });
});
