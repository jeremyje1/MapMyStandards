import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckIcon } from '@heroicons/react/24/outline';

interface PricingPlan {
  id: string;
  name: string;
  monthlyPrice: number;
  annualPrice: number;
  priceIds: {
    monthly: string;
    annual: string;
  };
  features: string[];
  popular?: boolean;
}

const pricingPlans: PricingPlan[] = [
  {
    id: 'starter',
    name: 'Starter',
    monthlyPrice: 99,
    annualPrice: 999,
    priceIds: {
      monthly: 'price_1RyVPPK8PKpLCKDZFbwkFdqq',
      annual: 'price_1RyVPgK8PKpLCKDZe8nu4ium'
    },
    features: [
      'Up to 100 documents',
      'Basic compliance tracking',
      'Monthly compliance reports',
      'Standard email support',
      '1 user account',
      'Basic analytics dashboard'
    ]
  },
  {
    id: 'professional',
    name: 'Professional',
    monthlyPrice: 299,
    annualPrice: 2999,
    priceIds: {
      monthly: 'price_1S1PIaK8PKpLCKDZxRRzTP59',
      annual: 'price_1S1PIkK8PKpLCKDZqxmtxUeG'
    },
    popular: true,
    features: [
      'Unlimited documents',
      'Advanced compliance tracking',
      'Real-time compliance reports',
      'Priority email & phone support',
      'Up to 10 user accounts',
      'API access',
      'Custom integrations',
      'Advanced analytics & insights',
      'Audit trail & compliance history'
    ]
  },
  {
    id: 'institution',
    name: 'Institution',
    monthlyPrice: 599,
    annualPrice: 5999,
    priceIds: {
      monthly: 'price_1RyVQgK8PKpLCKDZTais3Tyx',
      annual: 'price_1RyVQrK8PKpLCKDZUshqaOvZ'
    },
    features: [
      'Everything in Professional',
      'Unlimited user accounts',
      'White-label options',
      'Dedicated account manager',
      'Custom training sessions',
      'SLA guarantee (99.9% uptime)',
      'Advanced security features',
      'Custom reporting',
      'Priority implementation support'
    ]
  }
];

const PricingPage: React.FC = () => {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleProceedToCheckout = () => {
    if (!selectedPlan) {
      alert('Please select a plan');
      return;
    }
    if (!email) {
      alert('Please enter your email address');
      return;
    }

    const plan = pricingPlans.find(p => p.id === selectedPlan);
    if (!plan) return;

    setLoading(true);
    
    // Navigate to checkout with the selected plan
    const planKey = billingPeriod === 'annual' ? `${selectedPlan}_annual` : selectedPlan;
    navigate(`/checkout?email=${encodeURIComponent(email)}&plan=${planKey}`);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(price);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900">
            Choose Your Plan
          </h1>
          <p className="mt-4 text-xl text-gray-600">
            Start with a 14-day free trial. No credit card required.
          </p>
        </div>

        {/* Billing Period Toggle */}
        <div className="mt-8 flex justify-center">
          <div className="relative bg-gray-100 rounded-lg p-1">
            <div className="grid grid-cols-2">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  billingPeriod === 'monthly'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod('annual')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  billingPeriod === 'annual'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500'
                }`}
              >
                Annual
                <span className="ml-2 text-green-600 text-xs">Save 20%</span>
              </button>
            </div>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="mt-12 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {pricingPlans.map((plan) => {
            const price = billingPeriod === 'monthly' ? plan.monthlyPrice : plan.annualPrice;
            const period = billingPeriod === 'monthly' ? 'month' : 'year';
            
            return (
              <div
                key={plan.id}
                className={`relative rounded-lg shadow-lg bg-white p-8 cursor-pointer transition-all ${
                  plan.popular ? 'ring-2 ring-blue-500' : ''
                } ${selectedPlan === plan.id ? 'border-2 border-blue-500 transform scale-105' : 'hover:shadow-xl'}`}
                onClick={() => setSelectedPlan(plan.id)}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="inline-flex rounded-full bg-blue-500 px-4 py-1 text-sm font-semibold text-white">
                      RECOMMENDED
                    </span>
                  </div>
                )}

                <div className="text-center">
                  <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                  <div className="mt-4 flex items-baseline justify-center">
                    <span className="text-5xl font-extrabold text-gray-900">
                      {formatPrice(price)}
                    </span>
                    <span className="ml-2 text-xl text-gray-500">/{period}</span>
                  </div>
                  {billingPeriod === 'annual' && (
                    <p className="mt-2 text-sm text-green-600">
                      {formatPrice(plan.monthlyPrice * 12 - plan.annualPrice)} saved annually
                    </p>
                  )}
                </div>

                <ul className="mt-8 space-y-4">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="ml-3 text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`mt-8 w-full py-3 px-4 rounded-md font-medium transition-colors ${
                    selectedPlan === plan.id
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {selectedPlan === plan.id ? 'Selected' : 'Select Plan'}
                </button>
              </div>
            );
          })}
        </div>

        {/* Email and Checkout Section */}
        <div className="mt-12 max-w-md mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Enter your email to continue
            </h3>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@company.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <button
              onClick={handleProceedToCheckout}
              disabled={loading || !email || !selectedPlan}
              className="mt-4 w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Processing...' : 'Continue to Checkout'}
            </button>
            <p className="mt-4 text-sm text-gray-500 text-center">
              14-day free trial • Cancel anytime • Secure checkout
            </p>
          </div>
        </div>

        {/* Trust Badges */}
        <div className="mt-12 text-center">
          <p className="text-sm text-gray-500 mb-4">Trusted by leading institutions</p>
          <div className="flex justify-center space-x-8">
            <img src="/api/placeholder/100/40" alt="SSL Secured" className="h-10 opacity-50" />
            <img src="/api/placeholder/100/40" alt="PCI Compliant" className="h-10 opacity-50" />
            <img src="/api/placeholder/100/40" alt="SOC 2 Type II" className="h-10 opacity-50" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;