// filepath: market-research-platform/frontend/src/components/reports/ReportExport.jsx
// Export dropdown for downloading reports as PDF or DOCX.

import React, { useState } from 'react';
import { Download, FileText, File } from 'lucide-react';
import { exportReport, downloadBlob } from '../../services/api';

function ReportExport({ reportId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format) => {
    setIsOpen(false);
    setIsExporting(true);
    try {
      const blob = await exportReport(reportId, format);
      const filename = `report_${reportId}.${format}`;
      downloadBlob(blob, filename);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="report-export">
      <button
        className="btn btn--secondary"
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
      >
        <Download size={14} />
        {isExporting ? 'Exporting...' : 'Export'}
      </button>

      {isOpen && (
        <ul className="report-export__menu">
          <li>
            <button onClick={() => handleExport('pdf')}>
              <File size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
              Export as PDF
            </button>
          </li>
          <li>
            <button onClick={() => handleExport('docx')}>
              <FileText size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
              Export as Word (.docx)
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}

export default ReportExport;
