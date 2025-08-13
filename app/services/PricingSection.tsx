"use client";
import React from 'react';

interface Plan {
  key: string;
  name: string;
  monthly: number;
  annual: number;
  featured?: boolean;
  savings: string;
  custom?: boolean;
  features: string[];
  cta: { label: string; href: string };
}

const plans: Plan[] = [
  {
    key: 'college',
    name: 'A³E College Plan',
    monthly: 297,
    annual: 2970, // 2 months free (12 * 297 = 3564)
    savings: '$40,000-$80,000',
    features: [
      '✅ Complete A³E Engine Access',
      '🏛️ Higher Ed: SACSCOC, HLC, MSCHE, NECHE, WSCUC, NWCCU',
      '🏫 K-12: Cognia/AdvancED, WASC, NEASC, SACS CASI',
      '🎓 Specialized: AACSB, ABET, CCNE, CAEP, IB',
      '🤖 AI Document Analysis & Gap Detection',
      '🎨 Canvas LMS Integration',
      '� Compliance Dashboard & Evidence Mapping',
      '✉️ Email Support (4h response)',
      '🎯 7-Day Free Trial'
    ],
    cta: { label: '🚀 Start Monthly', href: 'https://mapmystandards.ai/checkout.html?plan=college_monthly' }
  },
  {
    key: 'multi',
    name: 'A³E Multi-Campus Plan',
    monthly: 897,
    annual: 8970, // savings relative to 12 * 897 = 10764
    featured: true,
    savings: '$100,000-$200,000',
    features: [
      '🌟 Everything in College Plan',
      '🏢 Unlimited Campus / Department Profiles',
      '�️ System-wide Compliance Dashboard',
      '� Cross-Campus Resource Sharing',
      '🧩 Multi-District Management Tools',
      '🏷️ White-Label Reports & Branding',
      '� API Access (10K calls/mo)',
      '⚡ Priority Implementation',
      '📞 Priority Support (2h response)'
    ],
    cta: { label: '💎 Start Monthly', href: 'https://mapmystandards.ai/checkout.html?plan=multicampus_monthly' }
  },
  {
    key: 'enterprise',
    name: 'Enterprise Solution',
    monthly: 0,
    annual: 0,
    custom: true,
    savings: '$200,000-$500,000',
    features: [
      '🏗️ Custom / Hybrid / On-Prem Deployment',
      '🔓 Unlimited API & Data Integration',
      '🛡️ 24/7 Dedicated Support SLA',
      '💻 Proprietary Feature Development',
      '🔒 Advanced Security / Compliance Add-ons',
      '🌍 International & Emerging Accreditor Support',
      '📡 Advanced Analytics & Benchmarking',
      '🎓 Executive Advisory & Governance Workshops'
    ],
    cta: { label: '🏆 Request Enterprise Proposal', href: 'https://mapmystandards.ai/contact/' }
  }
];

export default function PricingSection() {
  const [annual, setAnnual] = React.useState(false);

  return (
    <section className="py-24" aria-labelledby="pricing-heading">
      <div className="max-w-7xl mx-auto px-4">
        <h2 id="pricing-heading" className="text-center text-3xl md:text-4xl font-bold tracking-tight text-slate-800">💎 Investment in Institutional Excellence</h2>
        <p className="text-center max-w-2xl mx-auto mt-6 text-slate-600 font-medium">Transform operational overhead into competitive advantage. Every A³E plan delivers exponential ROI through streamlined compliance, enhanced credibility, and operational efficiency that compounds over time.</p>
        <p className="text-center mt-3 text-indigo-600 font-semibold">💰 Typical ROI: 300–500% within first year · 🎯 Average savings: $50K–$150K annually</p>
        <div className="mt-8 flex items-center justify-center">
          <div role="group" aria-label="Billing period selector" className="inline-flex rounded-full overflow-hidden border border-slate-200 bg-slate-100 text-sm">
            <button type="button" aria-pressed={!annual} onClick={() => setAnnual(false)} className={`px-4 py-2 font-semibold transition ${!annual ? 'bg-indigo-600 text-white' : 'text-slate-700 hover:text-slate-900'}`}>Monthly</button>
            <button type="button" aria-pressed={annual} onClick={() => setAnnual(true)} className={`px-4 py-2 font-semibold transition flex items-center gap-1 ${annual ? 'bg-indigo-600 text-white' : 'text-slate-700 hover:text-slate-900'}`}>Annual <span className="text-emerald-500 font-bold text-xs">Save 16%</span></button>
          </div>
        </div>
        <div className="grid gap-8 mt-14 md:grid-cols-3">
          {plans.map(plan => {
            const price = annual ? plan.annual : plan.monthly;
            return (
              <article key={plan.key} className={`relative rounded-2xl border-2 bg-white p-8 shadow-sm transition hover:-translate-y-1 ${plan.featured ? 'border-indigo-500 ring-2 ring-indigo-200' : 'border-slate-200'}`} aria-label={plan.name}>
                {plan.featured && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-4 py-1 text-xs font-semibold uppercase tracking-wide text-white shadow">Most Popular</div>
                )}
                <h3 className="text-xl font-bold text-slate-800 mb-1">{plan.name}</h3>
                <div className="flex items-end gap-2 mb-2">
                  <span className="text-4xl font-extrabold text-indigo-600">{plan.custom ? 'Custom' : `$${price.toLocaleString()}`}</span>
                  {!plan.custom && <span className="text-sm font-medium text-slate-500">{annual ? '/yr' : '/mo'}</span>}
                </div>
                {!plan.custom && (
                  <p className="text-sm text-slate-500 mb-4">or <span className="font-semibold text-indigo-600">{annual ? `$${Math.round(price/12).toLocaleString()}/mo effective` : `$${plan.annual.toLocaleString()}/year`}</span></p>
                )}
                <ul className="space-y-2 text-sm text-slate-700 mb-6">
                  {plan.features.map(f => (
                    <li key={f} className="pl-5 relative"><span className="absolute left-0 top-0.5 text-emerald-600">✓</span>{f}</li>
                  ))}
                </ul>
                {plan.custom ? (
                  <a href={plan.cta.href} className={`block w-full text-center font-semibold rounded-lg px-4 py-3 bg-indigo-600 hover:bg-indigo-500 text-white transition shadow`}>{plan.cta.label}</a>
                ) : (
                  <div className="space-y-3">
                    <a href={plan.cta.href} className={`block w-full text-center font-semibold rounded-lg px-4 py-3 ${plan.featured ? 'bg-indigo-600 hover:bg-indigo-500 text-white' : 'bg-indigo-500 hover:bg-indigo-400 text-white'} transition shadow`}>{plan.cta.label}</a>
                    <a href={plan.key === 'college' ? 'https://mapmystandards.ai/checkout.html?plan=college_yearly' : 'https://mapmystandards.ai/checkout.html?plan=multicampus_yearly'} className="block w-full text-center font-semibold rounded-lg px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white transition shadow">🔁 Choose Annual</a>
                  </div>
                )}
                <p className="text-xs text-slate-500 mt-3"><strong>Typical savings:</strong> {plan.savings} annually</p>
                {!plan.custom && (
                  <p className="text-[10px] text-slate-400 mt-1">Annual effective: ${plan.annual / 12 < 1 ? '' : Math.round(plan.annual / 12).toLocaleString()}/mo</p>
                )}
              </article>
            );
          })}
        </div>
        <div className="mt-16 text-center bg-gradient-to-r from-indigo-500 to-violet-600 rounded-2xl p-10 text-white shadow-lg">
          <h3 className="text-2xl font-bold mb-3">🎯 ROI Guarantee</h3>
          <p className="max-w-2xl mx-auto text-base md:text-lg font-medium mb-6">We're so confident in A³E's transformative value that we guarantee measurable ROI within your first accreditation cycle. If you don't see significant operational improvements and cost savings, we'll work with you until you do.</p>
          <a href="https://api.mapmystandards.ai/landing" className="inline-block bg-white text-indigo-600 font-semibold px-8 py-3 rounded-full shadow hover:shadow-md transition">Start Your Transformation</a>
        </div>
      </div>
    </section>
  );
}
