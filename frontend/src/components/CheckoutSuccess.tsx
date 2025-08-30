import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircleIcon } from '@heroicons/react/24/outline';
import api from '../services/api';

const CheckoutSuccess: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [accountCreated, setAccountCreated] = useState(false);
  
  const sessionId = searchParams.get('session_id');
  const email = searchParams.get('email') || '';

  useEffect(() => {
    // Verify the checkout session
    if (sessionId) {
      verifySession();
    }
  }, [sessionId]);

  const verifySession = async () => {
    try {
      const response = await api.billing.verifyCheckoutSession(sessionId);
      if (response.data.email) {
        // Session verified successfully
      }
    } catch (err) {
      console.error('Failed to verify session:', err);
    }
  };

  const handlePasswordSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Create user account with password
      await api.auth.completeRegistration({
        session_id: sessionId,
        email: email,
        password: password
      });

      setAccountCreated(true);
      
      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        navigate('/dashboard');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create account. Please try again.');
      setLoading(false);
    }
  };

  if (accountCreated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Account Created Successfully
            </h2>
            <p className="text-gray-600 mb-6">
              Redirecting you to your dashboard...
            </p>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Success Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center justify-center mb-6">
            <CheckCircleIcon className="h-12 w-12 text-green-500" />
          </div>
          <h1 className="text-3xl font-bold text-center text-gray-900 mb-4">
            Payment Successful
          </h1>
          <p className="text-center text-gray-600">
            Thank you for your subscription. Let's set up your account.
          </p>
        </div>

        {/* Password Setup Form */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Create Your Password
          </h2>
          
          <form onSubmit={handlePasswordSetup} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                disabled
                className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                required
                minLength={8}
              />
              <p className="mt-1 text-sm text-gray-500">
                Must be at least 8 characters long
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Creating Account...' : 'Complete Setup'}
            </button>
          </form>
        </div>

        {/* Getting Started Guide */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Getting Started with MapMyStandards
          </h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Step 1: Upload Your Documents</h3>
              <p className="text-gray-600">
                Start by uploading your institutional documents, policies, and procedures. 
                Our AI will analyze them against accreditation standards.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Step 2: Select Your Accreditor</h3>
              <p className="text-gray-600">
                Choose your accrediting body (SACSCOC, HLC, etc.) to match your documents 
                against the appropriate standards.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Step 3: Review Compliance Gaps</h3>
              <p className="text-gray-600">
                Our system will identify gaps in your compliance and provide actionable 
                recommendations for improvement.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Step 4: Generate Reports</h3>
              <p className="text-gray-600">
                Create comprehensive compliance reports for your accreditation reviews 
                and internal assessments.
              </p>
            </div>
          </div>

          <div className="mt-8 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Need Help?</h4>
            <p className="text-blue-700">
              Our support team is ready to assist you. Contact us at{' '}
              <a href="mailto:support@mapmystandards.com" className="underline">
                support@mapmystandards.com
              </a>{' '}
              or schedule a demo call with our team.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutSuccess;