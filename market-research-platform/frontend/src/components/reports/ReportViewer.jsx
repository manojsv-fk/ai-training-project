// filepath: market-research-platform/frontend/src/components/reports/ReportViewer.jsx
// In-app viewer for generated reports with markdown rendering.

import React from 'react';
import ReactMarkdown from 'react-markdown';
import ReportExport from './ReportExport';
import { BookOpen } from 'lucide-react';

function ReportViewer({ report }) {
  if (!report) {
    return (
      <div className="report-viewer report-viewer--empty">
        <div style={{ textAlign: 'center' }}>
          <BookOpen size={32} style={{ marginBottom: 8, opacity: 0.3 }} />
          <p>Select a report to view it here.</p>
        </div>
      </div>
    );
  }

  const formatType = (type) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <article className="report-viewer">
      <header className="report-viewer__header">
        <div>
          <h1 className="report-viewer__title">{report.title}</h1>
          <div className="report-viewer__meta">
            <span className="badge badge--type">{formatType(report.report_type)}</span>
            <span>&middot;</span>
            <span>{new Date(report.generated_at).toLocaleString()}</span>
            {report.is_scheduled && (
              <>
                <span>&middot;</span>
                <span className="badge badge--medium">Scheduled</span>
              </>
            )}
          </div>
        </div>
        <ReportExport reportId={report.id} />
      </header>

      <div className="report-viewer__body">
        <ReactMarkdown>{report.content || 'No content available.'}</ReactMarkdown>
      </div>

      {report.source_document_ids && report.source_document_ids.length > 0 && (
        <footer className="report-viewer__sources">
          <h3>Source Documents</h3>
          <ul>
            {report.source_document_ids.map((docId) => (
              <li key={docId}>Document #{docId}</li>
            ))}
          </ul>
        </footer>
      )}
    </article>
  );
}

export default ReportViewer;
