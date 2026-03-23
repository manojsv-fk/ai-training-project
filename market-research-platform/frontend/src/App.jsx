// filepath: market-research-platform/frontend/src/App.jsx
// Root application component. Sets up client-side routing and global layout.

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import TopNav from './components/layout/TopNav';
import StatusBar from './components/layout/StatusBar';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

// TODO: Add a loading/splash screen for initial data fetch
// TODO: Add global error boundary component

function App() {
  return (
    <BrowserRouter>
      {/* Top navigation bar — always visible */}
      <TopNav />

      {/* Main routed content area */}
      <main className="app-main">
        <Routes>
          {/* Default route → Dashboard (hybrid main panel + chat panel) */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />

          {/* TODO: Add 404 Not Found page */}
        </Routes>
      </main>

      {/* Status bar — always visible at bottom */}
      <StatusBar />
    </BrowserRouter>
  );
}

export default App;
