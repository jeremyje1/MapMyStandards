import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { 
  DocumentTextIcon, 
  ChartBarIcon, 
  AcademicCapIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

interface DashboardMetrics {
  documentsCount: number;
  reportsCount: number;
  complianceScore: number;
  recentActivity: Array<{
    id: string;
    type: string;
    description: string;
    timestamp: string;
  }>;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await api.dashboard.getOverview();
      setMetrics(response.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Welcome, {user?.name}</span>
              <button
                onClick={() => {/* Add logout logic */}}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Link
              to="/documents"
              className="flex flex-col items-center p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <CloudArrowUpIcon className="h-10 w-10 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Upload Document</span>
            </Link>
            
            <Link
              to="/reports"
              className="flex flex-col items-center p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <ChartBarIcon className="h-10 w-10 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Generate Report</span>
            </Link>
            
            <Link
              to="/standards"
              className="flex flex-col items-center p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <AcademicCapIcon className="h-10 w-10 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">View Standards</span>
            </Link>
            
            <Link
              to="/compliance"
              className="flex flex-col items-center p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <CheckCircleIcon className="h-10 w-10 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Compliance Check</span>
            </Link>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Documents</p>
                <p className="text-3xl font-bold text-gray-900">
                  {metrics?.documentsCount || 0}
                </p>
              </div>
              <DocumentTextIcon className="h-12 w-12 text-gray-400" />
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Reports</p>
                <p className="text-3xl font-bold text-gray-900">
                  {metrics?.reportsCount || 0}
                </p>
              </div>
              <ChartBarIcon className="h-12 w-12 text-gray-400" />
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Compliance Score</p>
                <p className="text-3xl font-bold text-gray-900">
                  {metrics?.complianceScore || 0}%
                </p>
              </div>
              {(metrics?.complianceScore || 0) >= 80 ? (
                <CheckCircleIcon className="h-12 w-12 text-green-400" />
              ) : (
                <ExclamationCircleIcon className="h-12 w-12 text-yellow-400" />
              )}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="px-6 py-4">
            {metrics?.recentActivity && metrics.recentActivity.length > 0 ? (
              <ul className="space-y-3">
                {metrics.recentActivity.map((activity) => (
                  <li key={activity.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        {activity.type === 'document' && (
                          <DocumentTextIcon className="h-5 w-5 text-gray-400" />
                        )}
                        {activity.type === 'report' && (
                          <ChartBarIcon className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                      <p className="ml-3 text-sm text-gray-900">{activity.description}</p>
                    </div>
                    <p className="text-sm text-gray-500">
                      {new Date(activity.timestamp).toLocaleDateString()}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No recent activity</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;