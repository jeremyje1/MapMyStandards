import React from 'react';
import dynamic from 'next/dynamic';
const PricingSection = dynamic(() => import('./PricingSection'), { ssr: true });

export const metadata = {
  title: 'Services & Pricing | A³E Accreditation Engine | MapMyStandards.ai',
  description: 'A³E accreditation operating system services & pricing: multi-accreditor AI engine, compliance automation, strategic consulting, and institutional transformation.',
  alternates: { canonical: 'https://mapmystandards.ai/services/' },
  openGraph: {
    title: 'A³E Services & Pricing | Accreditation Intelligence Platform',
    description: 'Compare A³E plans: College, Multi-Campus, and Enterprise solutions delivering 300–500% ROI via multi-accreditor AI compliance automation.',
    url: 'https://mapmystandards.ai/services/',
    type: 'website',
    images: [{ url: 'https://mapmystandards.ai/og-default.png', width: 1200, height: 630, alt: 'A³E Accreditation Engine' }]
  },
  twitter: {
    card: 'summary_large_image',
    title: 'A³E Services & Pricing',
    description: 'Multi-accreditor AI accreditation engine with compliance automation & strategic services.',
    images: ['https://mapmystandards.ai/og-default.png']
  }
};


export default function ServicesPage() {
  return (
    <div className="flex flex-col gap-32">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-r from-indigo-500 to-violet-600 text-white rounded-3xl px-6 py-28 shadow-lg">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold leading-tight tracking-tight">🎯 Complete Accreditation Operating System</h1>
          <p className="mt-6 text-lg md:text-xl font-medium text-indigo-50 max-w-3xl mx-auto">Transform your institution into an accreditation powerhouse with A³E—the comprehensive platform that becomes indispensable to your operations, maximizes ROI, and creates unshakeable competitive advantages.</p>
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <a href="https://api.mapmystandards.ai/landing" className="bg-white text-indigo-600 font-semibold px-8 py-4 rounded-full shadow hover:shadow-md transition">🚀 Start Free Trial</a>
            <a href="/customer_experience.html" className="backdrop-blur bg-white/10 hover:bg-white/20 text-white font-semibold px-8 py-4 rounded-full border border-white/30 transition">🔬 See Full Experience</a>
          </div>
        </div>
        <div className="absolute inset-0 pointer-events-none opacity-30 mix-blend-overlay bg-[radial-gradient(circle_at_30%_40%,rgba(255,255,255,0.4),transparent_60%)]" />
      </section>

      {/* Platform Overview */}
      <section className="max-w-7xl mx-auto px-4" aria-labelledby="platform-heading">
        <div className="grid md:grid-cols-2 gap-14 items-center">
          <div>
            <h2 id="platform-heading" className="text-3xl md:text-4xl font-bold mb-6 text-slate-800">🧠 Your Institutional AI Brain</h2>
            <p className="text-slate-600 leading-relaxed mb-4">A³E doesn't just analyze documents—it becomes your institution's central nervous system for accreditation intelligence. Once integrated, it transforms into indispensable infrastructure that maximizes operational efficiency and creates massive competitive advantages.</p>
            <p className="text-slate-600 leading-relaxed mb-6"><strong>Deep Integration = Maximum ROI:</strong> Built on AWS Bedrock with Claude AI, A³E uses comprehensive accreditation ontologies developed by former accreditation directors and peer reviewers who understand what institutions really need.</p>
            <ul className="space-y-3">
              {[
                '🔍 Intelligent document parsing with institutional memory preservation',
                '🎯 Multi-accreditor standard mapping with cross-referencing that saves 20-30 hours weekly',
                '📊 Automated gap analysis with actionable recommendations that ensure compliance',
                '📋 Citation verification and comprehensive audit trail generation',
                '🔒 FERPA-compliant processing with enterprise-grade security that protects institutional assets',
                '💎 Continuous learning that makes your institution smarter with every interaction'
              ].map(item => (
                <li key={item} className="pl-6 relative text-slate-700"> <span className="absolute left-0 top-0">⚡</span>{item}</li>
              ))}
            </ul>
            <div className="mt-8 p-6 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 text-white shadow">
              <h4 className="font-semibold text-white mb-2 text-lg">💰 ROI Reality Check</h4>
              <p className="text-indigo-50 text-sm md:text-base"><strong>Typical institution savings:</strong> $50,000-$150,000 annually through reduced administrative overhead, streamlined compliance, and enhanced report quality. Most see full ROI within 60-90 days.</p>
            </div>
          </div>
          <div className="h-full w-full bg-gradient-to-br from-fuchsia-400 to-rose-500 rounded-2xl flex items-center justify-center text-white p-10 shadow-xl">
            <div className="text-center space-y-2 text-sm md:text-base font-medium tracking-wide">
              <h3 className="text-xl font-semibold mb-4">🏗️ A³E Architecture</h3>
              <div className="flex flex-col items-center gap-1">
                <span>📄 Document Intelligence</span>
                <span className="opacity-70">⬇️</span>
                <span>🧠 AI Analysis Engine</span>
                <span className="opacity-70">⬇️</span>
                <span>📊 Comprehensive Reports</span>
                <span className="opacity-70">⬇️</span>
                <span>🎯 Institutional Success</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Accreditor Support */}
      <section className="bg-slate-50 py-24" aria-labelledby="accreditor-heading">
        <div className="max-w-7xl mx-auto px-4">
          <h2 id="accreditor-heading" className="text-center text-3xl md:text-4xl font-bold text-slate-800">🌟 Comprehensive Accreditor Mastery</h2>
          <p className="text-center max-w-3xl mx-auto mt-6 text-slate-600 font-medium"><strong>Unlike fragmented tools that create operational complexity,</strong> A³E provides complete coverage across ALL major accrediting bodies with specialized ontologies that make your institution's compliance capabilities unmatched in the sector.</p>
          <div className="mt-10 bg-gradient-to-r from-indigo-500 to-violet-600 text-white rounded-2xl p-10 shadow">
            <h3 className="text-xl font-semibold mb-3">🎯 Competitive Intelligence Advantage</h3>
            <p className="text-indigo-50">A³E's comprehensive coverage means you're not just compliant—you're strategically positioned with deep insights that give you significant advantages over institutions using fragmented, incomplete solutions.</p>
          </div>
          <div className="grid gap-6 mt-14 md:grid-cols-3 lg:grid-cols-3">{/* 6 cards auto-fit */}
            {[
              { title: '🏛️ Regional Powerhouses', body: 'SACSCOC, MSCHE, NECHE, HLC, NWCCU, WSCUC - Complete standard mapping with deep citation verification that ensures bulletproof compliance and maximizes institutional credibility.' },
              { title: '🎓 Specialized Excellence', body: 'AACSB, ABET, CAEP, APA, LCME - Program-specific standards with professional requirements analysis that positions your programs as industry leaders.' },
              { title: '🏢 State Compliance Mastery', body: 'SCHEV, HECC, CPE, and 47+ others - State authorization and compliance requirements seamlessly integrated, eliminating regulatory risk and administrative burden.' },
              { title: '🇺🇸 Federal Requirements Shield', body: 'Title IV, FERPA, ADA, IDEA - Federal compliance tracking with automated monitoring that protects institutional assets and ensures continuous compliance.' },
              { title: '🌍 Custom & International', body: 'Any accreditor, anywhere - Custom ontology development for international bodies, emerging accreditors, and unique institutional requirements. No limitation on growth.' },
              { title: '🔗 Strategic Cross-Mapping', body: 'Operational efficiency multiplier - Automated identification of overlapping requirements across multiple accrediting bodies, eliminating redundant work and maximizing resource efficiency.' }
            ].map(card => (
              <article key={card.title} className="bg-white rounded-xl shadow-sm p-6 border border-slate-200 hover:shadow-md transition">
                <h3 className="font-semibold text-slate-800 mb-2 text-lg">{card.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{card.body}</p>
              </article>
            ))}
          </div>
          <div className="mt-14 border-l-4 border-indigo-500 bg-white rounded-r-xl p-8 shadow-sm">
            <h4 className="text-indigo-600 font-semibold mb-2">📈 Institutional Advantage Reality</h4>
            <p className="text-slate-700 text-sm md:text-base"><strong>Institutions using A³E report 40-60% faster accreditation cycles, 80% reduction in compliance stress, and significantly enhanced institutional credibility.</strong> This isn't just software—it's competitive infrastructure.</p>
          </div>
        </div>
      </section>

      <PricingSection />

      {/* Strategic Add-ons */}
      <section className="py-24 bg-slate-50" aria-labelledby="addons-heading">
        <div className="max-w-7xl mx-auto px-4">
          <h2 id="addons-heading" className="text-center text-3xl md:text-4xl font-bold text-slate-800">🚀 Strategic Acceleration Services</h2>
          <p className="text-center max-w-3xl mx-auto mt-6 text-slate-600 font-medium"> <strong>Maximize your competitive advantage with expert guidance that transforms A³E from powerful tool into institutional game-changer.</strong> These services ensure you extract maximum value and create unshakeable operational dependencies.</p>
          <div className="grid gap-8 mt-14 md:grid-cols-2 lg:grid-cols-4">
            {[
              { title: '🎯 Accreditation Strategy Consulting', badge: 'Custom Investment', body: 'Transform your accreditation approach into competitive advantage. Expert consulting from former accreditation directors and peer reviewers who have guided 200+ successful cycles. Strategic planning, self-study optimization, and site visit mastery that positions your institution as a sector leader.', bullets: ['Strategic planning for maximum institutional impact', 'Self-study narrative optimization', 'Site visit preparation excellence', 'Competitive positioning vs peers'] },
              { title: '🛠️ Custom Ontology Development', badge: 'Strategic Investment', body: 'Create unique competitive advantages through specialized accreditor support. Custom evidence mapping and narrative templates for emerging standards, international bodies, or unique institutional requirements.', bullets: ['Specialized accreditor standard integration', 'Custom evidence mapping', 'Proprietary narrative templates', 'Ongoing evolution updates'] },
              { title: '🔒 Enterprise Security Enhancement', badge: 'Protection Investment', body: 'Bulletproof security for mission-critical operations. Enhanced FERPA-safe deployment with comprehensive compliance auditing and ongoing monitoring.', bullets: ['Enhanced security configuration & monitoring', 'Compliance audit & certification', 'Ongoing security assessment', 'Risk mitigation for sensitive data'] },
              { title: '🎓 Institutional Transformation Training', badge: 'Excellence Investment', body: 'Transform your team into accreditation powerhouses. Comprehensive training on platform optimization, strategic best practices, and organizational transformation.', bullets: ['Team training on advanced capabilities', 'Strategic best practices for ROI', 'Change management coaching', 'Ongoing optimization support'] }
            ].map(card => (
              <article key={card.title} className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-md transition flex flex-col">
                <div className="flex items-start justify-between gap-4">
                  <h3 className="text-lg font-semibold text-slate-800 leading-snug flex-1">{card.title}</h3>
                  <span className="text-xs font-semibold bg-rose-50 text-rose-600 px-2 py-1 rounded border border-rose-100 whitespace-nowrap">{card.badge}</span>
                </div>
                <p className="text-sm text-slate-600 mt-3 flex-1 leading-relaxed">{card.body}</p>
                <ul className="mt-4 space-y-2 text-sm text-slate-700">
                  {card.bullets.map(b => (
                    <li key={b} className="pl-5 relative"><span className="absolute left-0 top-0.5 text-indigo-500">•</span>{b}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
          <div className="mt-16 border-l-4 border-indigo-500 bg-white rounded-r-xl p-8 shadow-sm text-center md:text-left">
            <h4 className="text-indigo-600 font-semibold mb-2">💎 Strategic Advantage Reality</h4>
            <p className="text-slate-700 max-w-3xl mx-auto"><strong>Institutions that invest in these strategic services report 2-3x faster value realization, deeper operational integration, and significantly enhanced competitive positioning.</strong> This is how you transform A³E from software into institutional DNA.</p>
            <a href="https://mapmystandards.ai/contact/" className="inline-block mt-6 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3 rounded-full shadow transition">Discuss Strategic Acceleration</a>
          </div>
        </div>
      </section>

      {/* Footer (marketing) */}
      <footer className="mt-10 bg-slate-900 text-slate-300 rounded-3xl p-12" aria-labelledby="footer-heading">
        <h2 id="footer-heading" className="sr-only">Footer</h2>
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-10">
          <div>
            <h3 className="text-slate-100 font-semibold mb-3">Platform Access</h3>
            <ul className="space-y-2 text-sm">
              <li><a className="hover:text-white transition" href="https://api.mapmystandards.ai/landing">🚀 Start Free Trial</a></li>
              <li><a className="hover:text-white transition" href="/customer_experience.html">🔬 Customer Experience</a></li>
              <li><a className="hover:text-white transition" href="/institutional_dashboard.html">🏛️ Institutional Dashboard</a></li>
              <li><a className="hover:text-white transition" href="https://api.mapmystandards.ai/docs">🔧 API Documentation</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-slate-100 font-semibold mb-3">Value Resources</h3>
            <ul className="space-y-2 text-sm">
              <li><a className="hover:text-white transition" href="/features.html">📚 Complete Feature List</a></li>
              <li><a className="hover:text-white transition" href="/services.html">💰 ROI Calculator</a></li>
              <li><a className="hover:text-white transition" href="/about/">📖 Success Stories</a></li>
              <li><a className="hover:text-white transition" href="/contact/">🎯 Demo Request</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-slate-100 font-semibold mb-3">Support & Training</h3>
            <ul className="space-y-2 text-sm">
              <li><a className="hover:text-white transition" href="mailto:support@mapmystandards.ai">✉️ Technical Support</a></li>
              <li><a className="hover:text-white transition" href="/contact/">💬 Sales & Success</a></li>
              <li><a className="hover:text-white transition" href="/privacy-policy/">🔒 Security & Privacy</a></li>
              <li><a className="hover:text-white transition" href="/manual.html">📋 Complete User Guide</a></li>
            </ul>
          </div>
            <div>
            <h3 className="text-slate-100 font-semibold mb-3">Company</h3>
            <ul className="space-y-2 text-sm">
              <li><a className="hover:text-white transition" href="/about/">About A³E</a></li>
              <li><a className="hover:text-white transition" href="mailto:sales@mapmystandards.ai">Sales Inquiry</a></li>
            </ul>
            <p className="mt-4 font-semibold text-slate-200">NorthPath Strategies</p>
            <p className="text-xs text-slate-500 mt-1">Built by accreditation experts</p>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-slate-700/60 flex flex-col md:flex-row items-center justify-between gap-6 text-xs tracking-wide">
          <div className="text-left">
            <p>&copy; 2025 MapMyStandards.ai. All rights reserved.</p>
            <p><strong>A³E</strong> – The complete accreditation operating system</p>
          </div>
          <div className="text-right">
            <p className="font-semibold text-indigo-400">🎯 Comprehensive • Indispensable • High ROI</p>
            <p>Maximizing institutional value since 2024</p>
          </div>
        </div>
      </footer>

      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify({
          '@context': 'https://schema.org',
            '@type': 'Product',
            name: 'A³E Accreditation Engine',
            url: 'https://mapmystandards.ai/services/',
            description: 'Multi-accreditor AI accreditation & compliance automation platform with strategic consulting services.',
            brand: { '@type': 'Brand', name: 'MapMyStandards' },
            offers: [
              { '@type': 'Offer', name: 'A³E College Plan', price: '297', priceCurrency: 'USD', priceValidUntil: '2025-12-31', availability: 'https://schema.org/InStock', url: 'https://mapmystandards.ai/services/' },
              { '@type': 'Offer', name: 'A³E Multi-Campus Plan', price: '897', priceCurrency: 'USD', priceValidUntil: '2025-12-31', availability: 'https://schema.org/InStock', url: 'https://mapmystandards.ai/services/' }
            ]
        }) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify({
          '@context': 'https://schema.org', '@type': 'FAQPage', mainEntity: [
            { '@type': 'Question', name: 'What ROI do institutions typically see?', acceptedAnswer: { '@type': 'Answer', text: 'Typical ROI ranges from 300–500% in the first year with $50K–$150K annual operational savings.' }},
            { '@type': 'Question', name: 'Do you offer annual discounts?', acceptedAnswer: { '@type': 'Answer', text: 'Yes, annual billing includes two free months (16% discount) compared to monthly rates.' }}
          ] }) }}
      />
    </div>
  );
}
