// filepath: market-research-platform/frontend/src/pages/Dashboard.jsx
// Main landing page with hybrid layout: main panel (70%) + chat panel (30%).

import React from 'react';
import TrendCards from '../components/dashboard/TrendCards';
import RecentReports from '../components/dashboard/RecentReports';
import SourceFeed from '../components/dashboard/SourceFeed';
import ChatPanel from '../components/chat/ChatPanel';

function Dashboard() {
  return (
    <div className="dashboard">
      <div className="dashboard__main">
        <TrendCards filters={{}} />
        <RecentReports />
        <SourceFeed />
      </div>
      <ChatPanel />
    </div>
  );
}

export default Dashboard;
