/**
 * Helper to load browser IIFE modules for testing
 */
const fs = require('fs');
const path = require('path');

/**
 * Load a JavaScript module that uses IIFE pattern
 * @param {string} filePath - Path to the JS file (relative to project root)
 * @param {string} exportName - Name of the exported object (e.g., 'ApiService')
 * @returns {Object} - The exported module
 */
function loadModule(filePath, exportName) {
  const absolutePath = path.resolve(__dirname, '../../..', filePath);
  const code = fs.readFileSync(absolutePath, 'utf8');

  // Wrap code to capture the export using eval
  const wrappedCode = `(function() { ${code}; return ${exportName}; })()`;

  // eslint-disable-next-line no-eval
  return eval(wrappedCode);
}

module.exports = { loadModule };
