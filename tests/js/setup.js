/**
 * Jest Setup - Configure browser environment mocks
 */

// Mock fetch API
global.fetch = jest.fn();

// Reset mocks before each test
beforeEach(() => {
  fetch.mockClear();
});

// Mock console.error to reduce noise in tests (keeps log and warn)
const originalError = console.error;
global.console = {
  ...console,
  error: jest.fn()
};

// Restore console.error after all tests
afterAll(() => {
  global.console.error = originalError;
});

// Mock AbortController if needed
global.AbortController = class {
  constructor() {
    this.signal = { aborted: false };
  }
  abort() {
    this.signal.aborted = true;
  }
};

// Helper to create mock responses
global.mockFetchResponse = (data, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data)
  });
};

// Helper to create mock error responses
global.mockFetchError = (errorMessage) => {
  return Promise.reject(new Error(errorMessage));
};
