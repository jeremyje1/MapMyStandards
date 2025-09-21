import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from './Layout';
import api from '../services/api';
import { 
  DocumentTextIcon, 
  ChartBarIcon, 
  AcademicCapIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import ChecklistCoverageCard from './ChecklistCoverageCard';
import ReviewerPackAction from './ReviewerPackAction';

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
  const [lastPack, setLastPack] = useState<{ download_url?: string; path?: string } | null>(null);
  const [settings, setSettings] = useState<{ organization?: string; display_name?: string; primary_accreditor?: string; has_onboarded?: boolean } | null>(null);
  const [reviewQueue, setReviewQueue] = useState<any[]>([]);
  const [readiness, setReadiness] = useState<any | null>(null);
  const [risk, setRisk] = useState<any | null>(null);
  const [trend, setTrend] = useState<Array<{ date: string; coverage: number }>>([]);
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.mapmystandards.ai';
  const resolveApiUrl = (url?: string) => {
    if (!url) return '';
    if (/^https?:\/\//i.test(url)) return url;
    return `${API_BASE_URL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`;
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await api.dashboard.getOverview();
      setMetrics(response.data);
      // Fetch settings for last reviewer pack
      try {
        const { data } = await api.raw.get('/api/user/intelligence-simple/settings');
        if (data) setSettings(data);
        if (data?.last_reviewer_pack) setLastPack(data.last_reviewer_pack);
      } catch {}

      // Parallel fetch of intelligence-simple data
      try {
        const [reviewsRes, readinessRes, riskRes, trendRes] = await Promise.all([
          api.intelligenceSimple.listReviews({ limit: 5 }),
          api.intelligenceSimple.readinessScorecard(),
          api.intelligenceSimple.riskAggregate(),
          api.intelligenceSimple.metricsTimeseries(),
        ]);
        setReviewQueue(reviewsRes?.data?.items || reviewsRes?.data || []);
        setReadiness(readinessRes?.data || null);
        setRisk(riskRes?.data || null);
        const ts = trendRes?.data?.series || trendRes?.data || [];
        setTrend(Array.isArray(ts) ? ts.slice(-8) : []);
      } catch (e) {
        // Best-effort; keep page usable if any endpoint is missing
      }
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
    <Layout>
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

        {/* Getting Started */}
        <div className="mb-8 bg-white rounded-lg shadow p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="text-sm text-gray-500">Getting Started</div>
              <div className="text-lg font-semibold text-gray-900">
                Welcome{settings?.display_name || user?.name ? `, ${settings?.display_name || user?.name}` : ''}
              </div>
              <div className="text-sm text-gray-600">
                {settings?.organization ? settings.organization : 'Your institution'}{settings?.primary_accreditor ? ` • Accreditor: ${settings.primary_accreditor}` : ''}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Link to="/documents" className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">Upload Evidence</Link>
              <Link to="/standards" className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50">View Standards</Link>
              <a href="#reviewer-pack" className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50">Build Reviewer Pack</a>
              <Link to="/onboarding" className="px-3 py-2 text-sm text-primary-600 hover:text-primary-700">Update profile</Link>
            </div>
          </div>
        </div>

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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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

          {/* Checklist Coverage Card */}
          <ChecklistCoverageCard />
         </div>

        {/* Reviewer Pack quick action */}
        <section id="reviewer-pack">
          <ReviewerPackAction accreditor={settings?.primary_accreditor || undefined} />
        </section>

        {/* Role-tailored cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-medium text-gray-900">Reviewer Queue</h3>
              <a href="/reports" className="text-sm text-primary-600 hover:text-primary-700">Open</a>
            </div>
            <p className="text-sm text-gray-600">Track items awaiting review and update statuses.</p>
            <ul className="mt-4 space-y-2 text-sm text-gray-700" data-testid="review-queue">
              {reviewQueue && reviewQueue.length > 0 ? (
                reviewQueue.slice(0,5).map((r: any, idx: number) => (
                  <li key={r.id || idx} className="flex justify-between border-b border-gray-100 pb-2">
                    <span className="truncate max-w-xs">
                      {(r.title || r.standard_id || 'Pending item').toString()}
                    </span>
                    <span className="text-xs text-gray-500">{(r.status || 'pending').toString()}</span>
                  </li>
                ))
              ) : (
                <li className="text-gray-500 text-sm">No items in queue</li>
              )}
            </ul>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-medium text-gray-900">Director Readiness</h3>
              <a href="https://api.mapmystandards.ai/customer/dashboard" target="_blank" rel="noreferrer" className="text-sm text-primary-600 hover:text-primary-700">Details</a>
            </div>
            <p className="text-sm text-gray-600">Snapshot of coverage, gaps, and timing to ready.</p>
            <div className="mt-4 text-sm text-gray-700">
              <div className="flex justify-between">
                <span>Overall Coverage</span>
                <span className="font-medium" data-testid="readiness-coverage">{readiness?.coverage_percentage ?? '—'}%</span>
              </div>
              <div className="flex justify-between">
                <span>Critical Gaps</span>
                <span className="font-medium">{readiness?.critical_gaps ?? '—'}</span>
              </div>
              <div className="mt-3">
                <div className="text-xs text-gray-500 mb-1">Recent Trend</div>
                <div className="flex gap-1 items-end h-12" data-testid="readiness-trend">
                  {trend.length > 0 ? trend.map((p, i) => (
                    <div key={i} title={`${p.date}: ${p.coverage}%`} style={{ height: `${Math.max(4, Math.min(100, p.coverage)) / 10}rem` }} className="w-2 bg-primary-200" />
                  )) : <div className="text-xs text-gray-400">No data</div>}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-medium text-gray-900">Risk Insights</h3>
              <a href="/reports" className="text-sm text-primary-600 hover:text-primary-700">Explore</a>
            </div>
            <p className="text-sm text-gray-600">Top sections needing attention to reduce accreditation risk.</p>
            <ul className="mt-4 space-y-2 text-sm text-gray-700" data-testid="risk-list">
              {(risk?.top_risks || risk?.items || []).slice(0,5).map((x: any, idx: number) => (
                <li key={x.id || idx} className="flex justify-between border-b border-gray-100 pb-2">
                  <span className="truncate max-w-xs">{(x.title || x.standard_id || 'Risk area').toString()}</span>
                  <span className="text-xs text-gray-500">{(x.score ?? x.risk_score ?? '—').toString()}</span>
                </li>
              ))}
              {(!risk || ((risk.top_risks||risk.items||[]).length === 0)) && (
                <li className="text-gray-500 text-sm">No risk items</li>
              )}
            </ul>
          </div>
        </div>

        {lastPack && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-600">Last Reviewer Pack</div>
                <div className="text-xs text-gray-500 break-all">{lastPack.path}</div>
              </div>
              {lastPack.download_url ? (
                <a className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700" href={resolveApiUrl(lastPack.download_url)} target="_blank" rel="noreferrer">Download</a>
              ) : (
                <span className="text-xs text-gray-500">No download URL</span>
              )}
            </div>
          </div>
        )}

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
    </Layout>
  );
};

export default Dashboard;