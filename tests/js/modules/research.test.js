/**
 * ResearchManager Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock dependencies
global.UI = {
  getElement: jest.fn(selector => document.querySelector(selector)),
  showNotification: jest.fn()
};

global.ResearchPDFGenerator = {
  generate: jest.fn(() => ({})),
  generateAndDownload: jest.fn(() => true),
  getLastPDF: jest.fn(() => ({})),
  downloadLast: jest.fn(() => true),
  clearCache: jest.fn()
};

global.ApiService = {
  saveChat: jest.fn(() => Promise.resolve({ status: 'ok' }))
};

global.ChatManager = {
  reloadChatHistory: jest.fn()
};

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve())
  }
});

// Mock EventSource
class MockEventSource {
  constructor(url) {
    this.url = url;
    this.readyState = 0;
    this.listeners = {};
  }
  addEventListener(event, callback) {
    this.listeners[event] = callback;
  }
  close() {
    this.readyState = 2;
  }
  // Helper to trigger events in tests
  _trigger(event, data) {
    if (this.listeners[event]) {
      this.listeners[event]({ data: JSON.stringify(data) });
    }
  }
}
global.EventSource = MockEventSource;

// Mock DOM
document.body.innerHTML = `
  <form id="query-form">
    <input id="query-input" type="text" value="test query" />
    <select id="model-select">
      <option value="gpt-4">GPT-4</option>
    </select>
    <button type="submit">Send</button>
  </form>
  <div id="chat-container"></div>
`;

// Load sub-modules first (they create globals)
const ResearchPanel = loadModule('static/js/modules/research/research-panel.js', 'ResearchPanel');
const ResearchProgress = loadModule('static/js/modules/research/research-progress.js', 'ResearchProgress');
const ResearchExecutor = loadModule('static/js/modules/research/research-executor.js', 'ResearchExecutor');

// Make sub-modules available globally for the main module
global.ResearchPanel = ResearchPanel;
global.ResearchProgress = ResearchProgress;
global.ResearchExecutor = ResearchExecutor;

// Load main module
const ResearchManager = loadModule('static/js/modules/research/research.js', 'ResearchManager');

describe('ResearchManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    document.getElementById('chat-container').innerHTML = '';
    // Remove any existing panels
    const panel = document.getElementById('research-panel');
    if (panel) panel.remove();
    // Remove research button if exists
    const btn = document.getElementById('research-btn');
    if (btn) btn.remove();
  });

  describe('init', () => {
    test('should add research button to form', () => {
      ResearchManager.init();

      const researchBtn = document.getElementById('research-btn');
      expect(researchBtn).not.toBeNull();
    });

    test('should create research panel', () => {
      ResearchManager.init();

      const panel = document.getElementById('research-panel');
      expect(panel).not.toBeNull();
    });
  });

  describe('isInProgress', () => {
    test('should return false initially', () => {
      expect(ResearchManager.isInProgress()).toBe(false);
    });
  });

  describe('getResult', () => {
    test('should return null initially', () => {
      expect(ResearchManager.getResult()).toBeNull();
    });
  });

  describe('showPanel', () => {
    test('should make panel visible', () => {
      ResearchManager.init();
      ResearchManager.showPanel();

      const panel = document.getElementById('research-panel');
      expect(panel.classList.contains('hidden')).toBe(false);
    });
  });

  describe('hidePanel', () => {
    test('should hide the panel', () => {
      ResearchManager.init();
      ResearchManager.showPanel();
      ResearchManager.hidePanel();

      const panel = document.getElementById('research-panel');
      expect(panel.classList.contains('hidden')).toBe(true);
    });
  });

  describe('copySynthesizedAnswer', () => {
    test('should show notification when no results', async () => {
      await ResearchManager.copySynthesizedAnswer();

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('No research results')
      );
    });
  });

  describe('downloadPDF', () => {
    test('should show notification when no results', () => {
      ResearchManager.downloadPDF();

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('No research results')
      );
    });
  });

  describe('useInChat', () => {
    test('should show notification when no results', () => {
      ResearchManager.useInChat();

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('No research results')
      );
    });
  });
});

describe('ResearchPanel', () => {
  beforeEach(() => {
    const panel = document.getElementById('research-panel');
    if (panel) panel.remove();
  });

  test('should create panel with required elements', () => {
    const panel = ResearchPanel.create();

    expect(panel).not.toBeNull();
    expect(panel.id).toBe('research-panel');
    expect(panel.querySelector('#research-progress')).not.toBeNull();
    expect(panel.querySelector('#research-kb-list')).not.toBeNull();
    expect(panel.querySelector('#research-synthesis')).not.toBeNull();
  });

  test('should show and hide panel', () => {
    ResearchPanel.create();
    ResearchPanel.show();
    expect(ResearchPanel.isVisible()).toBe(true);

    ResearchPanel.hide();
    expect(ResearchPanel.isVisible()).toBe(false);
  });

  test('should reset panel state', () => {
    const panel = ResearchPanel.create();
    ResearchPanel.reset();

    expect(panel.querySelector('#research-progress-fill').style.width).toBe('0%');
    expect(panel.querySelector('#research-progress-text').textContent).toBe('Initializing...');
  });
});

describe('ResearchProgress', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="research-progress-steps"></div>
      <div id="research-progress-fill"></div>
      <div id="research-progress-text"></div>
      <div id="research-kb-list"></div>
      <div id="research-live-count">0/0 complete</div>
      <div id="research-synthesis" class="hidden"></div>
      <div id="research-synthesis-content"></div>
      <div id="research-total-sources"></div>
      <div id="research-total-time"></div>
      <div id="research-progress"></div>
      <div id="research-auto-status"></div>
    `;
  });

  test('should initialize progress steps', () => {
    ResearchProgress.initProgressSteps({ kb1: 'KB One', kb2: 'KB Two' });

    const steps = document.getElementById('research-progress-steps');
    expect(steps.children.length).toBe(2);
    expect(steps.querySelector('#progress-step-kb1')).not.toBeNull();
    expect(steps.querySelector('#progress-step-kb2')).not.toBeNull();
  });

  test('should update progress bar', () => {
    ResearchProgress.updateProgressBar(2, 4, 'Testing...');

    expect(document.getElementById('research-progress-fill').style.width).toBe('40%');
    expect(document.getElementById('research-progress-text').textContent).toBe('Testing...');
  });

  test('should add KB result card', () => {
    ResearchProgress.addKBResultCard({
      kb_key: 'test',
      kb_name: 'Test KB',
      success: true,
      response: 'Test response',
      doc_count: 5,
      query_time_ms: 1500
    });

    const kbList = document.getElementById('research-kb-list');
    expect(kbList.children.length).toBe(1);
    expect(kbList.querySelector('#kb-card-test')).not.toBeNull();
  });

  test('should show synthesis', () => {
    ResearchProgress.showSynthesis({
      synthesized_answer: 'Test answer',
      total_sources: 10,
      total_time_ms: 5000
    });

    expect(document.getElementById('research-synthesis').classList.contains('hidden')).toBe(false);
    expect(document.getElementById('research-synthesis-content').textContent).toBe('Test answer');
    expect(document.getElementById('research-total-sources').textContent).toBe('10 sources');
  });

  test('should add auto status', () => {
    ResearchProgress.addAutoStatus('save', true, 'Saved successfully');

    const autoStatus = document.getElementById('research-auto-status');
    expect(autoStatus.children.length).toBe(1);
    expect(autoStatus.querySelector('.success')).not.toBeNull();
  });
});
