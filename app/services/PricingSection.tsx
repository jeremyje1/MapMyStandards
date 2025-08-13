"use client";
import React from 'react';

interface Plan {
  key: string;
  name: string;
  annual: number | 'custom';
  effectiveMonthly?: string; // formatted
  featured?: boolean;
  blurb: string;
  features: string[];
  cta: { label: string; href: string };
  footnote?: string;
}

const plans: Plan[] = [
  {
    key: 'department',
    name: 'Department (Self‑Serve)',
    annual: 9000,
    effectiveMonthly: '~$900/mo',
    blurb: 'Focused accreditation execution for a single program or department.',
    features: [
      '1 standard set',
      'Up to 500 artifacts',
      '5 users',
      '1 AI narrative / quarter',
      'Evidence exports (PDF/Doc)',
      'Baseline analytics',
      'Email notifications'
    ],
    cta: { label: '🚀 Start Department', href: 'https://mapmystandards.ai/checkout.html?plan=department_annual' },
    footnote: 'Ideal starter for first accreditation cycle'
  },
  {
    key: 'campus',
    name: 'Campus (Team)',
    annual: 24000,
    effectiveMonthly: '~$2,000/mo',
    featured: true,
    blurb: 'Full institutional adoption with multi-program oversight.',
    features: [
      '3 standard sets',
      '3,000 artifacts',
      '15 users',
      'Unlimited AI narratives',
      'CSV/XLSX import tools',
      'Canvas LMS integration',
      'Email support (standard SLA)'
    ],
    cta: { label: '💎 Start Campus', href: 'https://mapmystandards.ai/checkout.html?plan=campus_annual' },
    footnote: 'Most institutions start here'
  },
  {
    key: 'system',
    name: 'System (Pro)',
    annual: 48000,
    effectiveMonthly: '~$4,000/mo',
    blurb: 'Scaled compliance infrastructure for multi-entity operations.',
    features: [
      '10 standard sets',
      'Soft-cap: "Unlimited" artifacts*',
      '40 users',
      'SSO (SAML/OIDC)',
      'API data connectors',
      'Quarterly progress review',
      'Priority support response'
    ],
    cta: { label: '� Start System', href: 'https://mapmystandards.ai/checkout.html?plan=system_annual' },
    footnote: 'Includes strategic onboarding'
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    annual: 'custom',
    blurb: 'Mission‑critical deployment with governance & executive reporting.',
    features: [
      'Multi-campus / system hierarchy',
      'Advanced SSO & provisioning',
      'Real-time connectors & ETL',
      'Premium support SLA',
      'Optional Power BI board packs',
      'Executive accreditation dashboards',
      'Co-development roadmap options'
    ],
    cta: { label: '🏆 Request Proposal', href: 'https://mapmystandards.ai/contact/' },
    footnote: 'Tailored pricing based on scope'
  }
];

export default function PricingSection() {
  return (
    <section className="py-24" aria-labelledby="pricing-heading">
      <div className="max-w-7xl mx-auto px-4">
        <h2 id="pricing-heading" className="text-center text-3xl md:text-4xl font-bold tracking-tight text-slate-800">💎 Annual Platform Investment</h2>
        <p className="text-center max-w-3xl mx-auto mt-6 text-slate-600 font-medium">Accreditation is deadline-driven & budgeted annually. A³E is priced annual-first to align with budgeting cycles and deliver compounding ROI. <strong className="text-slate-800">Most institutions realize 300–500% ROI in the first year</strong>.</p>
        <p className="text-center mt-4 text-indigo-600 font-semibold text-sm">Upload reuse + AI narrative generation amplifies scale across standard sets and cycles.</p>
        <div className="grid gap-8 mt-14 md:grid-cols-2 lg:grid-cols-4">
          {plans.map(plan => (
            <article key={plan.key} className={`relative rounded-2xl border-2 bg-white p-7 shadow-sm transition hover:-translate-y-1 ${plan.featured ? 'border-indigo-500 ring-2 ring-indigo-200' : 'border-slate-200'}`} aria-label={plan.name}>
              {plan.featured && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-4 py-1 text-[11px] font-semibold uppercase tracking-wide text-white shadow">Most Popular</div>
              )}
              <h3 className="text-lg font-bold text-slate-800 mb-1">{plan.name}</h3>
              <div className="flex items-end gap-2 mb-1">
                <span className="text-3xl font-extrabold text-indigo-600">{plan.annual === 'custom' ? '$75K+' : `$${(plan.annual as number).toLocaleString()}`}</span>
                {plan.annual !== 'custom' && <span className="text-xs font-medium text-slate-500">annual</span>}
              </div>
              {plan.effectiveMonthly && <p className="text-xs text-slate-500 mb-4">{plan.effectiveMonthly} effective</p>}
              <p className="text-xs text-slate-600 mb-4 leading-relaxed">{plan.blurb}</p>
              <ul className="space-y-2 text-xs text-slate-700 mb-5">
                {plan.features.map(f => (
                  <li key={f} className="pl-4 relative"><span className="absolute left-0 top-0.5 text-emerald-600">✓</span>{f}</li>
                ))}
              </ul>
              <a href={plan.cta.href} className={`block w-full text-center font-semibold rounded-lg px-4 py-2.5 ${plan.featured ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-indigo-500 hover:bg-indigo-400'} text-white transition shadow`}>{plan.cta.label}</a>
              {plan.footnote && <p className="text-[10px] text-slate-500 mt-3">{plan.footnote}</p>}
            </article>
          ))}
        </div>
        <div className="mt-8 text-center max-w-3xl mx-auto text-[11px] text-slate-500">* "Unlimited" artifacts operates under fair-use soft caps aligned to typical accreditation evidence volume; overages & expansion tiers available for high-ingest edge cases to keep costs predictable.</div>
        <div className="mt-16 text-center bg-gradient-to-r from-indigo-500 to-violet-600 rounded-2xl p-10 text-white shadow-lg">
          <h3 className="text-2xl font-bold mb-3">🎯 Execution Velocity Guarantee</h3>
          <p className="max-w-2xl mx-auto text-base md:text-lg font-medium mb-6">A³E compresses accreditation execution cycles and eliminates redundant manual effort. If you do not achieve measurable operational acceleration by your first major submission milestone, we continue advisory support at no additional cost until you do.</p>
          <a href="https://api.mapmystandards.ai/landing" className="inline-block bg-white text-indigo-600 font-semibold px-8 py-3 rounded-full shadow hover:shadow-md transition">Start Annual Deployment</a>
        </div>
      </div>
    </section>
  );
}
