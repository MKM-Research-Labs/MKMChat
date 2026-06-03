/**
 * MKM Research Labs - Research PDF Generator
 * 
 * Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
 * 
 * This software is provided under license by MKM Research Labs. 
 * Use, reproduction, distribution, or modification of this code is subject to the 
 * terms and conditions of the license agreement provided with this software.
 *
 * Handles PDF report generation for deep research results.
 * Requires jsPDF library to be loaded.
 */
const ResearchPDFGenerator = (() => {
  // Private properties
  let jsPDF = null;
  let lastGeneratedPDF = null;
  
  /**
   * Initialize jsPDF reference
   * @returns {boolean} - Whether jsPDF is available
   */
  const initJsPDF = () => {
    if (window.jspdf) {
      jsPDF = window.jspdf.jsPDF;
      return true;
    }
    console.warn('jsPDF library not loaded');
    return false;
  };
  
  /**
   * Check if PDF generation is available
   * @returns {boolean}
   */
  const isAvailable = () => {
    if (!jsPDF && !initJsPDF()) {
      return false;
    }
    return true;
  };
  
  /**
   * Generate a PDF report from research results
   * @param {Object} result - The research result object
   * @returns {Object|null} - jsPDF instance or null on failure
   */
  const generate = (result) => {
    if (!isAvailable()) {
      console.error('PDF generation not available - jsPDF not loaded');
      return null;
    }
    
    if (!result || !result.kb_results) {
      console.error('Invalid research result provided');
      return null;
    }
    
    try {
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
        compress: true
      });
      
      // Page dimensions
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 20;
      const headerHeight = 20;
      const footerHeight = 15;
      const lineHeight = 6;
      const contentWidth = pageWidth - (margin * 2);
      
      let currentPage = 1;
      let yPosition = margin;
      
      // ===== HELPER FUNCTIONS =====
      
      /**
       * Add header and footer to current page
       */
      const addHeaderFooter = (pageNum) => {
        // Header bar
        pdf.setFillColor(59, 130, 246);
        pdf.rect(0, 0, pageWidth, 12, 'F');
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(10);
        pdf.setTextColor(255, 255, 255);
        pdf.text('MKM Research Labs - Deep Research Report', margin, 8);
        
        // Footer
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(8);
        pdf.setTextColor(128, 128, 128);
        pdf.text(`Page ${pageNum}`, pageWidth - margin, pageHeight - 8, { align: 'right' });
        pdf.text(new Date().toLocaleDateString(), margin, pageHeight - 8);
      };
      
      /**
       * Check if we need a new page and add one if so
       */
      const checkNewPage = (neededHeight = lineHeight * 2) => {
        if (yPosition + neededHeight > pageHeight - footerHeight) {
          pdf.addPage();
          currentPage++;
          addHeaderFooter(currentPage);
          yPosition = headerHeight + margin;
          return true;
        }
        return false;
      };
      
      /**
       * Add text with automatic word wrap and pagination
       */
      const addText = (text, fontSize = 10, isBold = false, color = [0, 0, 0]) => {
        if (!text) return 0;
        
        pdf.setFont('helvetica', isBold ? 'bold' : 'normal');
        pdf.setFontSize(fontSize);
        pdf.setTextColor(...color);
        
        const lines = pdf.splitTextToSize(text, contentWidth);
        
        for (let i = 0; i < lines.length; i++) {
          checkNewPage();
          pdf.text(lines[i], margin, yPosition);
          yPosition += lineHeight * (fontSize / 10);
        }
        
        return lines.length;
      };
      
      /**
       * Add a section title with optional chapter number
       */
      const addSectionTitle = (title, chapterNum = null) => {
        checkNewPage(lineHeight * 4);
        yPosition += lineHeight;
        
        if (chapterNum !== null) {
          pdf.setFont('helvetica', 'bold');
          pdf.setFontSize(14);
          pdf.setTextColor(59, 130, 246);
          pdf.text(`Chapter ${chapterNum}: ${title}`, margin, yPosition);
        } else {
          pdf.setFont('helvetica', 'bold');
          pdf.setFontSize(16);
          pdf.setTextColor(59, 130, 246);
          pdf.text(title, margin, yPosition);
        }
        
        yPosition += lineHeight * 2;
        
        // Decorative underline
        pdf.setDrawColor(59, 130, 246);
        pdf.setLineWidth(0.5);
        pdf.line(margin, yPosition - lineHeight, pageWidth - margin, yPosition - lineHeight);
        yPosition += lineHeight;
      };
      
      /**
       * Add a status badge
       */
      const addStatusBadge = (success, docCount, timeMs) => {
        const statusColor = success ? [34, 197, 94] : [239, 68, 68];
        const statusText = success ? 'SUCCESS' : 'FAILED';
        
        pdf.setFillColor(...statusColor);
        pdf.roundedRect(margin, yPosition, 25, 6, 1, 1, 'F');
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(8);
        pdf.setTextColor(255, 255, 255);
        pdf.text(statusText, margin + 2, yPosition + 4.5);
        
        pdf.setTextColor(128, 128, 128);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`${docCount} documents | ${(timeMs/1000).toFixed(1)}s`, margin + 30, yPosition + 4.5);
        yPosition += 12;
      };
      
      /**
       * Add sources list
       */
      const addSources = (sources) => {
        if (!sources || sources.length === 0) return;
        
        yPosition += lineHeight;
        addText('Sources:', 11, true, [64, 64, 64]);
        yPosition += 2;
        
        sources.forEach(source => {
          checkNewPage();
          pdf.setFont('helvetica', 'normal');
          pdf.setFontSize(9);
          pdf.setTextColor(107, 114, 128);
          pdf.text(`• ${source.file} (p.${source.page})`, margin + 5, yPosition);
          yPosition += 5;
        });
      };
      
      // ===== BUILD THE PDF =====
      
      // ----- TITLE PAGE -----
      addHeaderFooter(1);
      yPosition = 60;
      
      // Main title
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(24);
      pdf.setTextColor(59, 130, 246);
      pdf.text('Deep Research Report', pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 15;
      
      // Query text
      pdf.setFont('helvetica', 'italic');
      pdf.setFontSize(12);
      pdf.setTextColor(64, 64, 64);
      const queryLines = pdf.splitTextToSize(`"${result.query}"`, contentWidth - 20);
      queryLines.forEach(line => {
        pdf.text(line, pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 7;
      });
      yPosition += 10;
      
      // Metadata
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(10);
      pdf.setTextColor(128, 128, 128);
      
      const timestamp = result.timestamp ? new Date(result.timestamp).toLocaleString() : new Date().toLocaleString();
      pdf.text(`Generated: ${timestamp}`, pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 6;
      pdf.text(`Model: ${result.model}`, pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 6;
      pdf.text(`Total Sources: ${result.total_sources} | Total Time: ${(result.total_time_ms/1000).toFixed(1)}s`, pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 20;
      
      // Table of Contents
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(14);
      pdf.setTextColor(0, 0, 0);
      pdf.text('Contents', margin, yPosition);
      yPosition += 10;
      
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(10);
      pdf.setTextColor(64, 64, 64);
      pdf.text('Executive Summary', margin + 10, yPosition);
      yPosition += 6;
      
      result.kb_results.forEach((kb, index) => {
        const status = kb.success ? '✓' : '✗';
        pdf.text(`Chapter ${index + 1}: ${kb.kb_name} ${status}`, margin + 10, yPosition);
        yPosition += 6;
      });
      
      // ----- EXECUTIVE SUMMARY -----
      pdf.addPage();
      currentPage++;
      addHeaderFooter(currentPage);
      yPosition = headerHeight + margin;
      
      addSectionTitle('Executive Summary');
      addText(result.synthesized_answer, 10, false, [32, 32, 32]);
      
      // ----- CHAPTERS FOR EACH KNOWLEDGE BASE -----
      result.kb_results.forEach((kb, index) => {
        pdf.addPage();
        currentPage++;
        addHeaderFooter(currentPage);
        yPosition = headerHeight + margin;
        
        addSectionTitle(kb.kb_name, index + 1);
        addStatusBadge(kb.success, kb.doc_count, kb.query_time_ms);
        
        // Response or error
        if (kb.success && kb.response) {
          addText('Response:', 11, true, [64, 64, 64]);
          yPosition += 2;
          addText(kb.response, 10, false, [32, 32, 32]);
        } else if (kb.error) {
          addText('Error:', 11, true, [239, 68, 68]);
          addText(kb.error, 10, false, [239, 68, 68]);
        } else {
          addText('No response available.', 10, true, [128, 128, 128]);
        }
        
        // Sources
        addSources(kb.sources);
      });
      
      // Store reference and return
      lastGeneratedPDF = pdf;
      return pdf;
      
    } catch (error) {
      console.error('PDF generation error:', error);
      return null;
    }
  };
  
  /**
   * Generate and immediately download the PDF
   * @param {Object} result - The research result object
   * @param {string} filename - Optional custom filename
   * @returns {boolean} - Whether download was successful
   */
  const generateAndDownload = (result, filename = null) => {
    const pdf = generate(result);
    
    if (!pdf) {
      return false;
    }
    
    // Build filename from query if not provided
    if (!filename) {
      const querySlug = result.query
        .substring(0, 30)
        .replace(/[^a-z0-9]/gi, '_')
        .toLowerCase();
      const dateStr = new Date().toISOString().slice(0, 10);
      filename = `research_${querySlug}_${dateStr}.pdf`;
    }
    
    pdf.save(filename);
    return true;
  };
  
  /**
   * Download the last generated PDF
   * @param {string} filename - Optional custom filename
   * @returns {boolean} - Whether download was successful
   */
  const downloadLast = (filename = null) => {
    if (!lastGeneratedPDF) {
      console.warn('No PDF has been generated yet');
      return false;
    }
    
    if (!filename) {
      const dateStr = new Date().toISOString().slice(0, 10);
      filename = `research_report_${dateStr}.pdf`;
    }
    
    lastGeneratedPDF.save(filename);
    return true;
  };
  
  /**
   * Get the last generated PDF instance
   * @returns {Object|null} - jsPDF instance or null
   */
  const getLastPDF = () => lastGeneratedPDF;
  
  /**
   * Clear the cached PDF
   */
  const clearCache = () => {
    lastGeneratedPDF = null;
  };
  
  // Public API
  return {
    /**
     * Initialize the PDF generator (call on page load)
     */
    init: initJsPDF,
    
    /**
     * Check if PDF generation is available
     */
    isAvailable,
    
    /**
     * Generate a PDF from research results
     * @param {Object} result - Research result object
     * @returns {Object|null} - jsPDF instance
     */
    generate,
    
    /**
     * Generate and download PDF in one step
     * @param {Object} result - Research result object
     * @param {string} filename - Optional filename
     * @returns {boolean} - Success status
     */
    generateAndDownload,
    
    /**
     * Download the last generated PDF
     * @param {string} filename - Optional filename
     * @returns {boolean} - Success status
     */
    downloadLast,
    
    /**
     * Get the last generated PDF instance
     * @returns {Object|null}
     */
    getLastPDF,
    
    /**
     * Clear the cached PDF
     */
    clearCache
  };
})();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    ResearchPDFGenerator.init();
  });
} else {
  ResearchPDFGenerator.init();
}
