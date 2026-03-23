// filepath: market-research-platform/frontend/src/components/layout/StatusBar.jsx
// Fixed bottom status bar showing system health indicators.

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStatus } from '../../services/api';

function StatusBar() {
  const { data } = useQuery({
    queryKey: ['status'],
    queryFn: getStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: false,
  });

  const docCount = data?.doc_count ?? 0;
  const lastSync = data?.last_sync
    ? new Date(data.last_sync).toLocaleTimeString()
    : 'Never';
  const indexStatus = data?.index_status ?? 'ready';

  return (
    <footer className="status-bar">
      <span className="status-bar__item">
        {docCount} document{docCount !== 1 ? 's' : ''} indexed
      </span>
      <span className="status-bar__divider">&middot;</span>
      <span className="status-bar__item">
        Last sync: {lastSync}
      </span>
      <span className="status-bar__divider">&middot;</span>
      <span className={`status-bar__item status-bar__item--${indexStatus}`}>
        {indexStatus === 'indexing' && <span className="loading-spinner" style={{ marginRight: 4 }} />}
        Index: {indexStatus}
      </span>
    </footer>
  );
}

export default StatusBar;
