// filepath: market-research-platform/frontend/src/components/documents/DocumentList.jsx
// Table listing all ingested documents with search, filter, and delete actions.

import React, { useState } from 'react';
import { Trash2, ExternalLink, FileText, Newspaper, CheckCircle, Clock } from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';

function DocumentList({ onSelect }) {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [page, setPage] = useState(1);

  const filters = { page, limit: 20 };
  if (search) filters.search = search;
  if (typeFilter) filters.source_type = typeFilter;

  const { documents, total, isLoading, deleteDocument, isDeleting } = useDocuments(filters);

  const handleDelete = (e, docId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this document?')) {
      deleteDocument(docId);
    }
  };

  const formatDate = (isoStr) => {
    return new Date(isoStr).toLocaleDateString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <section className="document-list">
      <div className="document-list__toolbar">
        <input
          className="document-list__search"
          type="text"
          placeholder="Search documents..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <select
          className="document-list__filter"
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Types</option>
          <option value="pdf_upload">PDFs</option>
          <option value="news_article">News</option>
        </select>
      </div>

      {isLoading ? (
        <div style={{ padding: 24 }}>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="skeleton" style={{ height: 20, marginBottom: 12, width: '100%' }} />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <div className="document-list__empty">
          <FileText size={32} style={{ marginBottom: 8, opacity: 0.3 }} />
          <p>No documents found. Upload a PDF to get started.</p>
        </div>
      ) : (
        <>
          <table className="document-list__table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Source</th>
                <th>Ingested</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} onClick={() => onSelect?.(doc)}>
                  <td>{doc.title}</td>
                  <td>
                    {doc.source_type === 'pdf_upload' ? (
                      <span className="badge badge--pdf">
                        <FileText size={10} style={{ marginRight: 2 }} /> PDF
                      </span>
                    ) : (
                      <span className="badge badge--news">
                        <Newspaper size={10} style={{ marginRight: 2 }} /> News
                      </span>
                    )}
                  </td>
                  <td>{doc.source_name || '—'}</td>
                  <td>{formatDate(doc.ingested_at)}</td>
                  <td>
                    {doc.has_embeddings ? (
                      <CheckCircle size={14} style={{ color: 'var(--color-success)' }} title="Indexed" />
                    ) : (
                      <Clock size={14} style={{ color: 'var(--color-warning)' }} title="Processing" />
                    )}
                  </td>
                  <td>
                    <button
                      className="btn btn--sm btn--danger"
                      onClick={(e) => handleDelete(e, doc.id)}
                      disabled={isDeleting}
                      title="Delete"
                    >
                      <Trash2 size={12} />
                    </button>
                    {doc.original_url && (
                      <a
                        href={doc.original_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn--sm btn--secondary"
                        style={{ marginLeft: 4 }}
                        onClick={(e) => e.stopPropagation()}
                        title="Open source"
                      >
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: 16 }}>
              <button
                className="btn btn--sm btn--secondary"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </button>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', alignSelf: 'center' }}>
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn--sm btn--secondary"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

export default DocumentList;
