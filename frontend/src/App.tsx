import React from 'react';
// Deploy with LIVE Stripe keys configured
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/Dashboard';
import StripeCheckout from './components/billing/StripeCheckout';
import CheckoutSuccess from './components/CheckoutSuccess';
import PricingPage from './components/PricingPage';
import Trial from './components/Trial';
import PrivateRoute from './components/PrivateRoute';
import Layout from './components/Layout';
import StandardsPage from './components/StandardsPage';
import ReportsPage from './components/ReportsPage';
import CrosswalkPage from './components/CrosswalkPage';
import Onboarding from './components/Onboarding';
import OnboardingGuard from './components/OnboardingGuard';
import UploadPage from './components/UploadPage';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/trial" element={<Trial />} />
          <Route path="/checkout" element={<StripeCheckout />} />
          <Route path="/checkout/success" element={<CheckoutSuccess />} />
          <Route path="/onboarding" element={<Onboarding />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={
            <PrivateRoute>
              <OnboardingGuard>
                <Layout><Dashboard /></Layout>
              </OnboardingGuard>
            </PrivateRoute>
          } />
          
          <Route path="/documents" element={
            <PrivateRoute>
              <Layout>
                <UploadPage />
              </Layout>
            </PrivateRoute>
          } />
          
          <Route path="/reports" element={
            <PrivateRoute>
              <Layout><ReportsPage /></Layout>
            </PrivateRoute>
          } />

          <Route path="/standards" element={
            <PrivateRoute>
              <Layout><StandardsPage /></Layout>
            </PrivateRoute>
          } />

          <Route path="/crosswalk" element={
            <PrivateRoute>
              <Layout><CrosswalkPage /></Layout>
            </PrivateRoute>
          } />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;