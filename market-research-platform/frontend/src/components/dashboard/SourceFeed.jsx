// filepath: market-research-platform/frontend/src/components/dashboard/SourceFeed.jsx
// Live feed of recently ingested sources with type badges and timestamps.

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Rss, RefreshCw, FileText, Newspaper } from 'lucide-react';
import { listDocuments, triggerNewsSync } from '../../services/api';

function SourceFeed() {
  const [filter, setFilter] = useState('all');
  const [syncing, setSyncing] = useState(false);

  const params = { limit: 20, page: 1 };
  if (filter !== 'all') params.source_type = filter;

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['documents-feed', params],
    queryFn: () => listDocuments(params),
    refetchInterval: 30000,
  });

  const sources = data?.documents || [];

  const handleSync = async () => {
    setSyncing(true);
    try {
      await triggerNewsSync();
      refetch();
    } catch (err) {
      console.error('News sync failed:', err);
    } finally {
      setSyncing(false);
    }
  };

  const formatTime = (isoStr) => {
    const date = new Date(isoStr);
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <section className="source-feed">
      <div className="source-feed__header">
        <h2>
          <Rss size={18} style={{ marginRight: 6, verticalAlign: -3 }} />
          Ingested Sources
        </h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {['all', 'pdf_upload', 'news_article'].map(f => (
            <button
              key={f}
              className={`btn btn--sm ${filter === f ? 'btn--primary' : 'btn--secondary'}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f === 'pdf_upload' ? 'PDFs' : 'News'}
            </button>
          ))}
          <button
            className="btn btn--sm btn--secondary"
            onClick={handleSync}
            disabled={syncing}
          >
            <RefreshCw size={12} className={syncing ? 'loading-spinner' : ''} />
            Sync News
          </button>
        </div>
      </div>

      {isLoading ? (
        <div>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="skeleton" style={{ height: 20, marginBottom: 8, width: '100%' }} />
          ))}
        </div>
      ) : sources.length === 0 ? (
        <p className="source-feed__empty">
          No sources ingested yet. Upload a PDF or sync news to get started.
        </p>
      ) : (
        <ul className="source-feed__list">
          {sources.map((source) => (
            <li key={source.id} className="source-feed__item">
              {source.source_type === 'pdf_upload' ? (
                <span className="badge badge--pdf">
                  <FileText size={10} style={{ marginRight: 2 }} /> PDF
                </span>
              ) : (
                <span className="badge badge--news">
                  <Newspaper size={10} style={{ marginRight: 2 }} /> News
                </span>
              )}
              <span className="source-feed__name">{source.title}</span>
              <span className="source-feed__meta">
                {source.source_name} &middot; {formatTime(source.ingested_at)}
              </span>
              {!source.has_embeddings && (
                <span className="loading-spinner" title="Indexing..." />
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default SourceFeed;
