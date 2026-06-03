/**
 * MKM Research Labs - Visualization Charts Module
 *
 * Handles Chart.js initialization and chart rendering.
 *
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 */
const VisualizationCharts = (() => {
  // Track chart instances for cleanup
  let chartInstances = {};

  /**
   * Initialize Chart.js library
   * @returns {Promise<boolean>} - Whether Chart.js was loaded successfully
   */
  const initChartLibrary = async () => {
    // Check if Chart.js is already available
    if (window.Chart) {
      return true;
    }

    // Load Chart.js from CDN
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js';
      script.onload = () => resolve(true);
      script.onerror = () => {
        console.error('Failed to load Chart.js');
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification('Failed to load visualization library');
        }
        reject(false);
      };
      document.head.appendChild(script);
    });
  };

  /**
   * Destroy existing chart instance if it exists
   * @param {string} canvasId - Canvas element ID
   */
  const destroyChart = (canvasId) => {
    if (chartInstances[canvasId]) {
      chartInstances[canvasId].destroy();
      delete chartInstances[canvasId];
    }
  };

  /**
   * Render source distribution chart
   * @param {string} canvasId - Canvas element ID
   * @param {Array} data - Source distribution data
   */
  const renderSourceDistribution = (canvasId, data) => {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;

    destroyChart(canvasId);

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(item => item.name),
        datasets: [{
          label: 'Citations',
          data: data.map(item => item.count),
          backgroundColor: '#8884d8',
          borderColor: '#7771d8',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const item = data[context.dataIndex];
                return `Pages: ${item.pages}`;
              }
            }
          },
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Distribution by Source'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Number of Citations'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Source'
            }
          }
        }
      }
    });
  };

  /**
   * Render date distribution chart
   * @param {string} canvasId - Canvas element ID
   * @param {Array} data - Date distribution data
   */
  const renderDateDistribution = (canvasId, data) => {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;

    destroyChart(canvasId);

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(item => item.name),
        datasets: [{
          label: 'Citations',
          data: data.map(item => item.count),
          backgroundColor: '#82ca9d',
          borderColor: '#6ebb89',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: 'Distribution by Date'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Number of Citations'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Time Period'
            }
          }
        }
      }
    });
  };

  /**
   * Render relevance distribution chart
   * @param {string} canvasId - Canvas element ID
   * @param {Array} data - Relevance distribution data
   */
  const renderRelevanceDistribution = (canvasId, data) => {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;

    destroyChart(canvasId);

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: data.map(item => item.name),
        datasets: [{
          data: data.map(item => item.value),
          backgroundColor: [
            '#00C49F', '#0088FE', '#FFBB28', '#FF8042'
          ],
          borderColor: [
            '#00b38e', '#0077e8', '#eead25', '#ee753c'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
          },
          title: {
            display: true,
            text: 'Distribution by Relevance'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.raw;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = Math.round((value / total) * 100);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  };

  /**
   * Render keyword cloud
   * @param {string} containerId - Container element ID
   * @param {Array} data - Keyword data
   */
  const renderKeywordCloud = (containerId, data) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Clear existing content
    container.innerHTML = '';

    // Calculate max and min values for scaling
    const maxValue = Math.max(...data.map(item => item.value));
    const minValue = Math.min(...data.map(item => item.value));

    // Color palette
    const colors = [
      '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28AFF',
      '#8884d8', '#82ca9d', '#FF6B6B', '#F8E16C', '#4D908E'
    ];

    // Create keyword elements
    data.forEach((keyword, index) => {
      // Calculate size based on value (normalized between 0.8 and 2.0)
      const size = 0.8 + ((keyword.value - minValue) / (maxValue - minValue)) * 1.2;

      const keywordEl = document.createElement('div');
      keywordEl.className = 'inline-block px-3 py-1 m-1 rounded-full text-white';
      keywordEl.style.fontSize = `${size}rem`;
      keywordEl.style.backgroundColor = colors[index % colors.length];
      keywordEl.style.opacity = 0.7 + (keyword.value / (maxValue * 2));
      keywordEl.textContent = keyword.text;

      // Add click handler to filter by keyword
      keywordEl.addEventListener('click', () => {
        if (typeof UI !== 'undefined' && UI.showNotification) {
          UI.showNotification(`Filtering by keyword: ${keyword.text}`);
        }
        // In a real implementation, this would filter the results
      });

      container.appendChild(keywordEl);
    });
  };

  /**
   * Destroy all chart instances
   */
  const destroyAllCharts = () => {
    Object.keys(chartInstances).forEach(canvasId => {
      destroyChart(canvasId);
    });
  };

  // Public API
  return {
    init: initChartLibrary,
    renderSourceDistribution,
    renderDateDistribution,
    renderRelevanceDistribution,
    renderKeywordCloud,
    destroyAllCharts
  };
})();
