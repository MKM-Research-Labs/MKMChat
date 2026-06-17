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
