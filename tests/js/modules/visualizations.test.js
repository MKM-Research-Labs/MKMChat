/**
 * VisualizationManager Tests
 */

const { loadModule } = require('../helpers/loadModule');

// Mock dependencies
global.UI = {
  getElement: jest.fn(selector => document.querySelector(selector)),
  showNotification: jest.fn()
};

global.ChatManager = {
  getChatMessages: jest.fn(() => [])
};

// Mock Chart.js
global.Chart = jest.fn(function(ctx, config) {
  this.ctx = ctx;
  this.config = config;
  this.destroy = jest.fn();
});
global.window = { Chart: global.Chart };

// Mock DOM
document.body.innerHTML = `
  <div id="chat-container"></div>
`;

// Load sub-modules first (they create globals)
const VisualizationData = loadModule('static/js/modules/visualizations/visualization-data.js', 'VisualizationData');
const VisualizationCharts = loadModule('static/js/modules/visualizations/visualization-charts.js', 'VisualizationCharts');
const VisualizationPanel = loadModule('static/js/modules/visualizations/visualization-panel.js', 'VisualizationPanel');

// Make sub-modules available globally for the main module
global.VisualizationData = VisualizationData;
global.VisualizationCharts = VisualizationCharts;
global.VisualizationPanel = VisualizationPanel;

// Load main module
const VisualizationManager = loadModule('static/js/modules/visualizations/visualizations.js', 'VisualizationManager');

describe('VisualizationManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    document.getElementById('chat-container').innerHTML = '';
    // Remove existing viz container
    const vizContainer = document.getElementById('query-visualization-container');
    if (vizContainer) vizContainer.remove();
  });

  describe('init', () => {
    test('should initialize without errors', () => {
      expect(() => VisualizationManager.init()).not.toThrow();
    });

    test('should add CSS styles to document', () => {
      VisualizationManager.init();

      const styleElements = document.querySelectorAll('style');
      const hasVizStyles = Array.from(styleElements).some(
        style => style.textContent.includes('visualize-btn')
      );
      expect(hasVizStyles).toBe(true);
    });
  });

  describe('attachVisualizationToMessage', () => {
    test('should add visualize button to assistant messages', () => {
      const messageElement = document.createElement('div');
      messageElement.className = 'message-wrapper';

      VisualizationManager.attachVisualizationToMessage(messageElement, 0, 'assistant');

      const button = messageElement.querySelector('.visualize-btn');
      expect(button).not.toBeNull();
      expect(button.textContent).toBe('Visualize');
    });

    test('should not add button to user messages', () => {
      const messageElement = document.createElement('div');
      messageElement.className = 'message-wrapper';

      VisualizationManager.attachVisualizationToMessage(messageElement, 0, 'user');

      const button = messageElement.querySelector('.visualize-btn');
      expect(button).toBeNull();
    });

    test('should not add duplicate buttons', () => {
      const messageElement = document.createElement('div');
      messageElement.className = 'message-wrapper';

      VisualizationManager.attachVisualizationToMessage(messageElement, 0, 'assistant');
      VisualizationManager.attachVisualizationToMessage(messageElement, 0, 'assistant');

      const buttons = messageElement.querySelectorAll('.visualize-btn');
      expect(buttons.length).toBe(1);
    });
  });

  describe('visualizeQueryResults', () => {
    test('should show notification when no messages', async () => {
      ChatManager.getChatMessages.mockReturnValueOnce([]);

      await VisualizationManager.visualizeQueryResults(0);

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('No chat messages')
      );
    });

    test('should show notification when no sources found', async () => {
      ChatManager.getChatMessages.mockReturnValueOnce([
        { role: 'user', content: 'Test query' },
        { role: 'assistant', content: 'Test response' }
      ]);

      await VisualizationManager.visualizeQueryResults(1);

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('No sources')
      );
    });

    test('should analyze and visualize when sources exist', async () => {
      ChatManager.getChatMessages.mockReturnValueOnce([
        { role: 'user', content: 'Test query' },
        { role: 'assistant', content: 'Test response' },
        { role: 'sources', content: 'Sources:\n• doc1.pdf (p.1, 2)\n• doc2.pdf (p.3)' }
      ]);

      // Mock fetch for API call
      global.fetch = jest.fn(() => Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          totalResults: 3,
          topSources: [{ name: 'doc1', count: 2, pages: 2 }],
          relevanceDistribution: [{ name: 'High', value: 3 }],
          dateDistribution: [{ name: '2023', count: 3 }],
          topKeywords: [{ text: 'test', value: 3 }]
        })
      }));

      await VisualizationManager.visualizeQueryResults(1);

      expect(UI.showNotification).toHaveBeenCalledWith(
        expect.stringContaining('Analyzing')
      );
    });
  });
});

describe('VisualizationData', () => {
  test('should parse sources correctly', () => {
    const sources = [
      { file: '/path/to/doc2023.pdf', page: '1' },
      { file: '/path/to/doc2023.pdf', page: '2' },
      { file: '/path/to/other2020.pdf', page: '5' }
    ];

    const result = VisualizationData.parse(sources);

    expect(result).not.toBeNull();
    expect(result.totalResults).toBe(3);
    expect(result.topSources.length).toBeGreaterThan(0);
    expect(result.relevanceDistribution.length).toBe(4);
  });

  test('should return null for empty sources', () => {
    expect(VisualizationData.parse([])).toBeNull();
    expect(VisualizationData.parse(null)).toBeNull();
  });
});

describe('VisualizationPanel', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="chat-container"></div>';
  });

  test('should create visualization container', () => {
    const container = VisualizationPanel.create();

    expect(container).not.toBeNull();
    expect(container.id).toBe('query-visualization-container');
    expect(container.querySelector('#chart-relevance')).not.toBeNull();
    expect(container.querySelector('#chart-sources')).not.toBeNull();
  });

  test('should show and hide container', () => {
    VisualizationPanel.create();

    VisualizationPanel.show();
    const container = document.getElementById('query-visualization-container');
    expect(container.classList.contains('hidden')).toBe(false);

    VisualizationPanel.hide();
    expect(container.classList.contains('hidden')).toBe(true);
  });

  test('should add visualization button to element', () => {
    const element = document.createElement('div');
    const onClick = jest.fn();

    VisualizationPanel.addVisualizationButton(element, onClick);

    const button = element.querySelector('.visualize-btn');
    expect(button).not.toBeNull();
    expect(button.textContent).toBe('Visualize');
  });
});

describe('VisualizationCharts', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <canvas id="test-chart"></canvas>
      <div id="test-cloud"></div>
    `;
  });

  test('should render source distribution chart', () => {
    const data = [
      { name: 'doc1', count: 5, pages: 3 },
      { name: 'doc2', count: 3, pages: 2 }
    ];

    VisualizationCharts.renderSourceDistribution('test-chart', data);

    expect(Chart).toHaveBeenCalled();
  });

  test('should render keyword cloud', () => {
    const data = [
      { text: 'keyword1', value: 10 },
      { text: 'keyword2', value: 5 }
    ];

    VisualizationCharts.renderKeywordCloud('test-cloud', data);

    const container = document.getElementById('test-cloud');
    expect(container.children.length).toBe(2);
  });
});
