import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Upload', to: '/documents' },
  { label: 'Standards Explorer', to: '/standards' },
  { label: 'Reports', to: '/reports' },
  // Aliases requested to always show
  { label: 'Reviewer Portal', to: '/reports' },
  { label: 'Admin Standards', to: '/standards' },
  { label: 'CrosswalkX', to: '/crosswalk' },
  { label: 'Org Chart', to: '/org-chart' },
  { label: 'Scenario Modeling', to: '/scenario-modeling' },
  { label: 'Help', to: '/help' },
  { label: 'Advanced Dashboard', to: 'https://api.mapmystandards.ai/customer/dashboard' },
];

const Layout: React.FC<{ children: React.ReactNode } > = ({ children }) => {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/dashboard" className="text-xl font-bold text-gray-900">MapMyStandards</Link>
            <nav className="flex flex-wrap gap-4 text-sm">
              {navItems.map((item) => {
                const active = location.pathname.startsWith(item.to);
                // External link support
                const isExternal = /^https?:\/\//i.test(item.to);
                return isExternal ? (
                  <a
                    key={item.label + item.to}
                    href={item.to}
                    target="_blank"
                    rel="noreferrer"
                    className={(active ? 'text-primary-600' : 'text-gray-600') + ' hover:text-primary-700 transition-colors'}
                  >
                    {item.label}
                  </a>
                ) : (
                  <Link
                    key={item.label + item.to}
                    to={item.to}
                    className={
                      (active ? 'text-primary-600' : 'text-gray-600') +
                      ' hover:text-primary-700 transition-colors'
                    }
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
    </div>
  );
};

export default Layout;
