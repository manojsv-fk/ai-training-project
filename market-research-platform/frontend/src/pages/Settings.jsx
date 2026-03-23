// filepath: market-research-platform/frontend/src/pages/Settings.jsx
// Application settings page with news config, scheduling, and API key status.

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, CheckCircle, XCircle } from 'lucide-react';
import * as api from '../services/api';

function Settings() {
  const queryClient = useQueryClient();
  const [localTopics, setLocalTopics] = useState('');
  const [localInterval, setLocalInterval] = useState(60);
  const [initialized, setInitialized] = useState(false);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: api.getSettings,
    onSuccess: (data) => {
      if (!initialized) {
        setLocalTopics(data.news_topics || '');
        setLocalInterval(data.news_sync_interval_minutes || 60);
        setInitialized(true);
      }
    },
  });

  // Initialize local state from fetched data
  if (settings && !initialized) {
    setLocalTopics(settings.news_topics || '');
    setLocalInterval(settings.news_sync_interval_minutes || 60);
    setInitialized(true);
  }

  const updateMutation = useMutation({
    mutationFn: api.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });

  const handleSaveNews = () => {
    updateMutation.mutate({
      news_topics: localTopics,
      news_sync_interval_minutes: localInterval,
    });
  };

  const apiKeys = settings?.api_keys_configured || {};

  return (
    <div className="settings-page">
      <header className="settings-page__header">
        <h1>Settings</h1>
      </header>

      {/* News Ingestion */}
      <section className="settings-page__section">
        <h2>News Ingestion</h2>
        <label>
          Topics / Keywords (comma-separated)
          <input
            type="text"
            value={localTopics}
            onChange={(e) => setLocalTopics(e.target.value)}
            placeholder="e.g. supply chain, AI, logistics"
          />
        </label>
        <label>
          Sync Interval
          <select
            value={localInterval}
            onChange={(e) => setLocalInterval(Number(e.target.value))}
          >
            <option value={15}>Every 15 minutes</option>
            <option value={30}>Every 30 minutes</option>
            <option value={60}>Every hour</option>
            <option value={360}>Every 6 hours</option>
            <option value={1440}>Daily</option>
          </select>
        </label>
        <button
          className="btn btn--primary"
          onClick={handleSaveNews}
          disabled={updateMutation.isPending}
          style={{ marginTop: 8 }}
        >
          <Save size={14} />
          {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
        </button>
        {updateMutation.isSuccess && (
          <span style={{ color: 'var(--color-success)', fontSize: '0.875rem', marginLeft: 12 }}>
            <CheckCircle size={14} style={{ verticalAlign: -2, marginRight: 4 }} />
            Saved
          </span>
        )}
      </section>

      {/* Scheduled Reports */}
      <section className="settings-page__section">
        <h2>Scheduled Reports</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: 12 }}>
          Weekly briefs are generated automatically based on the configured cron schedule.
        </p>
        <label>
          Schedule (cron)
          <input
            type="text"
            defaultValue={settings?.weekly_brief_cron || '0 8 * * 1'}
            placeholder="0 8 * * 1 (Monday 8am)"
            disabled
          />
        </label>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
          Cron schedule editing will be available in a future update.
        </p>
      </section>

      {/* Model Configuration */}
      <section className="settings-page__section">
        <h2>Model Configuration</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <label>
            LLM Model
            <input type="text" value={settings?.openai_model || ''} disabled />
          </label>
          <label>
            Embedding Model
            <input type="text" value={settings?.embedding_model || ''} disabled />
          </label>
          <label>
            Chunk Size
            <input type="text" value={settings?.chunk_size || ''} disabled />
          </label>
          <label>
            Retrieval Top K
            <input type="text" value={settings?.retrieval_top_k || ''} disabled />
          </label>
        </div>
      </section>

      {/* API Key Status */}
      <section className="settings-page__section">
        <h2>API Keys</h2>
        <p className="settings-page__note">
          API keys are configured via the <code>.env</code> file and cannot be changed here.
        </p>
        <div className="settings-page__key-status">
          <div className="settings-page__key-item">
            <span className={`settings-page__key-dot ${apiKeys.openai ? 'settings-page__key-dot--ok' : 'settings-page__key-dot--missing'}`} />
            <span>OpenAI</span>
            {apiKeys.openai ? (
              <CheckCircle size={12} style={{ color: 'var(--color-success)' }} />
            ) : (
              <XCircle size={12} style={{ color: 'var(--color-danger)' }} />
            )}
          </div>
          <div className="settings-page__key-item">
            <span className={`settings-page__key-dot ${apiKeys.llama_cloud ? 'settings-page__key-dot--ok' : 'settings-page__key-dot--missing'}`} />
            <span>LlamaParse</span>
            {apiKeys.llama_cloud ? (
              <CheckCircle size={12} style={{ color: 'var(--color-success)' }} />
            ) : (
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>(optional)</span>
            )}
          </div>
          <div className="settings-page__key-item">
            <span className={`settings-page__key-dot ${apiKeys.newsapi ? 'settings-page__key-dot--ok' : 'settings-page__key-dot--missing'}`} />
            <span>NewsAPI</span>
            {apiKeys.newsapi ? (
              <CheckCircle size={12} style={{ color: 'var(--color-success)' }} />
            ) : (
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>(optional)</span>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

export default Settings;
