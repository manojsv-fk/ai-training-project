// filepath: market-research-platform/frontend/src/components/dashboard/RecentReports.jsx
// Lists the most recently generated reports with View and Export actions.

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Download, Eye } from 'lucide-react';
import { listReports, exportReport, downloadBlob } from '../../services/api';
import { useNavigate } from 'react-router-dom';

function RecentReports() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ['reports', { limit: 5, sort: 'newest' }],
    queryFn: () => listReports({ limit: 5, sort: 'newest' }),
  });

  const reports = data?.reports || [];

  const handleView = (report) => {
    navigate('/reports', { state: { selectedReportId: report.id } });
  };

  const handleExport = async (reportId, format) => {
    try {
      const blob = await exportReport(reportId, format);
      downloadBlob(blob, `report_${reportId}.${format}`);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const formatType = (type) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <section className="recent-reports">
      <div className="recent-reports__header">
        <h2>
          <BookOpen size={18} style={{ marginRight: 6, verticalAlign: -3 }} />
          Recent Reports
        </h2>
        <button className="btn btn--sm btn--primary" onClick={() => navigate('/reports')}>
          Generate New
        </button>
      </div>

      {isLoading ? (
        <div style={{ padding: 16 }}>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: 20, marginBottom: 12, width: '100%' }} />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <p className="recent-reports__empty">
          No reports generated yet. Select documents and generate your first summary.
        </p>
      ) : (
        <table className="recent-reports__table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Type</th>
              <th>Generated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td>{report.title}</td>
                <td><span className="badge badge--type">{formatType(report.report_type)}</span></td>
                <td>{new Date(report.generated_at).toLocaleDateString()}</td>
                <td>
                  <button
                    className="btn btn--sm btn--secondary"
                    onClick={() => handleView(report)}
                    title="View report"
                  >
                    <Eye size={12} />
                  </button>
                  <button
                    className="btn btn--sm btn--secondary"
                    onClick={() => handleExport(report.id, 'pdf')}
                    title="Export as PDF"
                    style={{ marginLeft: 4 }}
                  >
                    <Download size={12} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default RecentReports;
