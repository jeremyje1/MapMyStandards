import React from 'react';
// Trigger Railway deployment - nodejs only
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/Dashboard';
import StripeCheckout from './components/billing/StripeCheckout';
import Trial from './components/Trial';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/trial" element={<Trial />} />
          <Route path="/checkout" element={<StripeCheckout />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          } />
          
          <Route path="/documents" element={
            <PrivateRoute>
              <div className="min-h-screen bg-gray-50 p-8">
                <h1 className="text-3xl font-bold">Documents</h1>
              </div>
            </PrivateRoute>
          } />
          
          <Route path="/reports" element={
            <PrivateRoute>
              <div className="min-h-screen bg-gray-50 p-8">
                <h1 className="text-3xl font-bold">Reports</h1>
              </div>
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