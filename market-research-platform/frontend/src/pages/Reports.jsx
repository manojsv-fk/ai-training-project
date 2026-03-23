// filepath: market-research-platform/frontend/src/pages/Reports.jsx
// Reports page with list, viewer, and generation modal.

import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { Plus, BookOpen, Loader } from 'lucide-react';
import ReportViewer from '../components/reports/ReportViewer';
import * as api from '../services/api';

function Reports() {
  const location = useLocation();
  const queryClient = useQueryClient();
  const [selectedReport, setSelectedReport] = useState(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  // Fetch all reports
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ['reports-list'],
    queryFn: () => api.listReports({ limit: 50 }),
  });

  const reports = reportsData?.reports || [];

  // Fetch all documents for the generation modal
  const { data: docsData } = useQuery({
    queryKey: ['documents-for-report'],
    queryFn: () => api.listDocuments({ limit: 100 }),
    enabled: showGenerateModal,
  });

  const allDocuments = docsData?.documents || [];

  // Handle navigation state (e.g., from dashboard "View" button)
  useEffect(() => {
    if (location.state?.selectedReportId && reports.length > 0) {
      const report = reports.find(r => r.id === location.state.selectedReportId);
      if (report) {
        // Fetch full report content
        api.getReport(report.id).then(setSelectedReport);
      }
    }
  }, [location.state, reports]);

  const handleSelectReport = async (report) => {
    const fullReport = await api.getReport(report.id);
    setSelectedReport(fullReport);
  };

  const formatType = (type) =>
    type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="reports-page">
      <header className="reports-page__header">
        <h1>Reports</h1>
        <button className="btn btn--primary" onClick={() => setShowGenerateModal(true)}>
          <Plus size={14} /> Generate Report
        </button>
      </header>

      <div className="reports-page__layout">
        <aside className="reports-page__list">
          {reportsLoading ? (
            <div style={{ padding: 16 }}>
              {[1, 2, 3].map(i => (
                <div key={i} className="skeleton" style={{ height: 40, marginBottom: 8 }} />
              ))}
            </div>
          ) : reports.length === 0 ? (
            <div style={{ padding: 16, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
              No reports yet. Click "Generate Report" to create your first one.
            </div>
          ) : (
            <ul>
              {reports.map((r) => (
                <li
                  key={r.id}
                  className={`reports-page__list-item ${selectedReport?.id === r.id ? 'active' : ''}`}
                  onClick={() => handleSelectReport(r)}
                >
                  <span>{r.title}</span>
                  <div className="reports-page__list-item__meta">
                    <span className="badge badge--type">{formatType(r.report_type)}</span>
                    <span>{new Date(r.generated_at).toLocaleDateString()}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <main className="reports-page__viewer">
          <ReportViewer report={selectedReport} />
        </main>
      </div>

      {/* Report Generation Modal */}
      {showGenerateModal && (
        <GenerateReportModal
          documents={allDocuments}
          onClose={() => setShowGenerateModal(false)}
          onGenerated={(report) => {
            setSelectedReport(report);
            setShowGenerateModal(false);
            queryClient.invalidateQueries({ queryKey: ['reports-list'] });
            queryClient.invalidateQueries({ queryKey: ['reports'] });
          }}
        />
      )}
    </div>
  );
}

// ── Report Generation Modal ──────────────────────────────────────────────────
function GenerateReportModal({ documents, onClose, onGenerated }) {
  const [title, setTitle] = useState('Executive Summary');
  const [reportType, setReportType] = useState('executive_summary');
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const toggleDoc = (id) => {
    setSelectedDocIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const report = await api.generateReport({
        title,
        report_type: reportType,
        document_ids: selectedDocIds,
      });
      onGenerated(report);
    } catch (err) {
      console.error('Report generation failed:', err);
      setIsGenerating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Generate Report</h2>
          <button className="modal__close" onClick={onClose}>&times;</button>
        </div>

        <div className="modal__body">
          <label style={{ display: 'block', marginBottom: 16 }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>Title</span>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                display: 'block', width: '100%', marginTop: 4,
                background: 'var(--color-bg-input)', border: '1px solid var(--color-border)',
                borderRadius: 6, padding: '8px 12px', color: 'var(--color-text-primary)',
                fontSize: '0.875rem',
              }}
            />
          </label>

          <label style={{ display: 'block', marginBottom: 16 }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>Report Type</span>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              style={{
                display: 'block', width: '100%', marginTop: 4,
                background: 'var(--color-bg-input)', border: '1px solid var(--color-border)',
                borderRadius: 6, padding: '8px 12px', color: 'var(--color-text-primary)',
                fontSize: '0.875rem',
              }}
            >
              <option value="executive_summary">Executive Summary</option>
              <option value="trend_report">Trend Report</option>
              <option value="custom">Custom</option>
            </select>
          </label>

          <div style={{ marginBottom: 16 }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 8 }}>
              Source Documents (optional — leave empty to use all)
            </span>
            {documents.length === 0 ? (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                No documents available. Upload documents first.
              </p>
            ) : (
              <div style={{ maxHeight: 200, overflowY: 'auto', border: '1px solid var(--color-border)', borderRadius: 6, padding: 8 }}>
                {documents.map(doc => (
                  <label key={doc.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', fontSize: '0.875rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={selectedDocIds.includes(doc.id)}
                      onChange={() => toggleDoc(doc.id)}
                    />
                    <span>{doc.title}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      ({doc.source_type === 'pdf_upload' ? 'PDF' : 'News'})
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="modal__actions">
          <button className="btn btn--secondary" onClick={onClose}>Cancel</button>
          <button
            className="btn btn--primary"
            onClick={handleGenerate}
            disabled={isGenerating || !title.trim()}
          >
            {isGenerating ? (
              <>
                <Loader size={14} className="loading-spinner" />
                Generating...
              </>
            ) : (
              <>
                <BookOpen size={14} />
                Generate
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Reports;
