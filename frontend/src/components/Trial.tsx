import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckIcon } from '@heroicons/react/24/outline';

const plans = [
  {
    id: 'starter',
    name: 'Starter',
    price: '$97',
    period: 'month',
    features: [
      'Up to 100 documents',
      'Basic compliance tracking',
      'Monthly reports',
      'Email support',
      '1 user account',
    ],
  },
  {
    id: 'professional',
    name: 'Professional',
    price: '$297',
    period: 'month',
    popular: true,
    features: [
      'Unlimited documents',
      'Advanced compliance tracking',
      'Real-time reports',
      'Priority support',
      'Up to 10 user accounts',
      'API access',
      'Custom integrations',
    ],
  },
  {
    id: 'institution',
    name: 'Institution',
    price: '$997',
    period: 'month',
    features: [
      'Everything in Professional',
      'Unlimited user accounts',
      'White-label options',
      'Dedicated account manager',
      'Custom training',
      'SLA guarantee',
    ],
  },
];

const Trial: React.FC = () => {
  const [selectedPlan, setSelectedPlan] = useState('professional');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleStartTrial = async () => {
    if (!email) {
      alert('Please enter your email address');
      return;
    }

    setLoading(true);
    // Redirect to Stripe checkout with trial parameters
    const checkoutUrl = `/checkout?email=${encodeURIComponent(email)}&plan=${selectedPlan}&trial=true`;
    navigate(checkoutUrl);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900">
            Start Your 14-Day Free Trial
          </h1>
          <p className="mt-4 text-xl text-gray-600">
            No credit card required. Full access to all features.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="mt-12 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`relative rounded-lg shadow-lg bg-white p-8 ${
                plan.popular ? 'ring-2 ring-primary-600' : ''
              } ${selectedPlan === plan.id ? 'border-2 border-primary-600' : ''}`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="inline-flex rounded-full bg-primary-600 px-4 py-1 text-sm font-semibold text-white">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                <div className="mt-4 flex items-baseline justify-center">
                  <span className="text-5xl font-extrabold text-gray-900">
                    {plan.price}
                  </span>
                  <span className="ml-2 text-xl text-gray-500">/{plan.period}</span>
                </div>
              </div>

              <ul className="mt-8 space-y-4">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start">
                    <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span className="ml-3 text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => setSelectedPlan(plan.id)}
                className={`mt-8 w-full py-3 px-4 rounded-md font-medium ${
                  selectedPlan === plan.id
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}
              >
                {selectedPlan === plan.id ? 'Selected' : 'Select Plan'}
              </button>
            </div>
          ))}
        </div>

        {/* Email Form */}
        <div className="mt-12 max-w-md mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Enter your email to start your trial
            </h3>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              required
            />
            <button
              onClick={handleStartTrial}
              disabled={loading || !email}
              className="mt-4 w-full py-3 px-4 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Start Free Trial'}
            </button>
            <p className="mt-4 text-sm text-gray-500 text-center">
              No credit card required • Cancel anytime
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Trial;