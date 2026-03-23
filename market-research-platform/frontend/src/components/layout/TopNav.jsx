// filepath: market-research-platform/frontend/src/components/layout/TopNav.jsx
// Top navigation bar with logo and primary nav links.

import React from 'react';
import { NavLink } from 'react-router-dom';
import { BarChart3, FileText, BookOpen, Settings } from 'lucide-react';

function TopNav() {
  return (
    <nav className="top-nav">
      <div className="top-nav__brand">
        <span className="top-nav__logo">MRIP</span>
        <span className="top-nav__title">Market Intelligence</span>
      </div>

      <ul className="top-nav__links">
        <li>
          <NavLink to="/dashboard">
            <BarChart3 size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
            Dashboard
          </NavLink>
        </li>
        <li>
          <NavLink to="/documents">
            <FileText size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
            Documents
          </NavLink>
        </li>
        <li>
          <NavLink to="/reports">
            <BookOpen size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
            Reports
          </NavLink>
        </li>
        <li>
          <NavLink to="/settings">
            <Settings size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
            Settings
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}

export default TopNav;
