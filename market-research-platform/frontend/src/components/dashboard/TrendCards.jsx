// filepath: market-research-platform/frontend/src/components/dashboard/TrendCards.jsx
// Grid of identified market trend cards with confidence badges.

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, RefreshCw } from 'lucide-react';
import { listTrends, triggerTrendAnalysis } from '../../services/api';

function TrendCards({ filters = {} }) {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['trends', filters],
    queryFn: () => listTrends(filters),
    refetchInterval: 60000,
  });

  const trends = data?.trends || [];

  const handleAnalyze = async () => {
    try {
      await triggerTrendAnalysis();
      refetch();
    } catch (err) {
      console.error('Trend analysis failed:', err);
    }
  };

  const getConfidenceBadge = (score) => {
    if (score >= 0.8) return { label: 'HIGH', className: 'badge--high' };
    if (score >= 0.5) return { label: 'MEDIUM', className: 'badge--medium' };
    return { label: 'LOW', className: 'badge--low' };
  };

  return (
    <section className="trend-cards">
      <div className="trend-cards__header">
        <h2>
          <TrendingUp size={18} style={{ marginRight: 6, verticalAlign: -3 }} />
          Key Trends
        </h2>
        <button className="btn btn--sm btn--secondary" onClick={handleAnalyze}>
          <RefreshCw size={12} />
          Analyze
        </button>
      </div>

      {isLoading ? (
        <div className="trend-cards__grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="trend-card">
              <div className="skeleton" style={{ height: 20, width: '60%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 40, width: '100%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 14, width: '40%' }} />
            </div>
          ))}
        </div>
      ) : trends.length === 0 ? (
        <div className="trend-cards__empty">
          <TrendingUp size={32} style={{ marginBottom: 8, opacity: 0.3 }} />
          <p>No trends identified yet. Upload documents and click "Analyze" to get started.</p>
        </div>
      ) : (
        <div className="trend-cards__grid">
          {trends.map((trend) => {
            const badge = getConfidenceBadge(trend.confidence_score);
            return (
              <div key={trend.id} className="trend-card">
                <div className="trend-card__header">
                  <h3>{trend.title}</h3>
                  <span className={`badge ${badge.className}`}>{badge.label}</span>
                </div>
                <p>{trend.description}</p>
                <div className="trend-card__meta">
                  {trend.tags && trend.tags.length > 0 && (
                    <span>{trend.tags.slice(0, 3).join(', ')}</span>
                  )}
                  <span>
                    {new Date(trend.identified_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default TrendCards;
