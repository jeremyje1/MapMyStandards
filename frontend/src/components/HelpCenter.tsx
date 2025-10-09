import React, { useEffect, useMemo, useState } from 'react';
import {
  LifebuoyIcon,
  BookOpenIcon,
  DocumentTextIcon,
  ArrowTopRightOnSquareIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import api from '../services/api';

type HelpMetadata = {
  formulas?: Record<
    string,
    {
      label: string;
      description: string;
      formula?: string;
      range?: string;
      aliases?: string[];
    }
  >;
  docs?: {
    faq?: string;
    documentation?: string;
    contact?: string;
  };
};

type Article = {
  id: string;
  title: string;
  description: string;
  href: string;
  category: 'technical' | 'guides' | 'support';
  tags: string[];
};

const staticArticles: Article[] = [
  {
    id: 'architecture-overview',
    title: 'Platform Architecture Overview',
    description:
      'Understand the ingestion pipeline, evidence AI, and analytics services that power MapMyStandards.',
    href: 'https://github.com/jeremyje1/MapMyStandards/blob/main/ARCHITECTURE_OVERVIEW.md',
    category: 'technical',
    tags: ['whitepaper', 'architecture'],
  },
  {
    id: 'api-quickstart',
    title: 'API Quickstart & Endpoint Catalog',
    description:
      'Review authentication flow, available endpoints, and payload examples for integrating with the platform.',
    href: 'https://github.com/jeremyje1/MapMyStandards/blob/main/API_ENDPOINTS_IMPLEMENTATION.md',
    category: 'technical',
    tags: ['api', 'integration'],
  },
  {
    id: 'data-privacy',
    title: 'Data Privacy & Security Posture',
    description:
      'Dive into how we handle customer data, retention policies, and security controls across the stack.',
    href: 'https://github.com/jeremyje1/MapMyStandards/blob/main/DATA_PRIVACY_RESPONSE.md',
    category: 'guides',
    tags: ['compliance', 'privacy'],
  },
  {
    id: 'rollout-playbook',
    title: 'Implementation & Rollout Playbook',
    description:
      'Step-by-step checklist for preparing accreditation evidence, onboarding reviewers, and measuring coverage.',
    href: 'https://github.com/jeremyje1/MapMyStandards/blob/main/DEPLOYMENT_GUIDE.md',
    category: 'guides',
    tags: ['onboarding', 'process'],
  },
  {
    id: 'contact-support',
    title: 'Contact Customer Success',
    description:
      'Reach our team for live assistance, troubleshooting, or bespoke workflow walkthroughs.',
    href: 'mailto:support@mapmystandards.ai',
    category: 'support',
    tags: ['support', 'human'],
  },
];

const fallbackMetadata: HelpMetadata = {
  docs: {
    faq: 'https://platform.mapmystandards.ai/faq',
    documentation: 'https://platform.mapmystandards.ai/docs',
    contact: 'mailto:support@mapmystandards.ai',
  },
};

const HelpCenter: React.FC = () => {
  const [metadata, setMetadata] = useState<HelpMetadata>(fallbackMetadata);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    let isMounted = true;

    const fetchMetadata = async () => {
      setLoading(true);
      try {
        const { data } = await api.intelligenceSimple.getUiHelp();
        if (isMounted && data) {
          setMetadata(data);
        }
      } catch (err) {
        console.warn('Failed to load help metadata, falling back to defaults.', err);
        if (isMounted) {
          setError('Using offline help resources while connectivity is restored.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchMetadata();

    return () => {
      isMounted = false;
    };
  }, []);

  const augmentedArticles = useMemo(() => {
    const docLinks: Article[] = [];

    if (metadata.docs?.documentation) {
      docLinks.push({
        id: 'product-docs',
        title: 'Product Documentation Portal',
        description: 'Browse live product docs, release notes, and implementation detail.',
        href: metadata.docs.documentation,
        category: 'technical',
        tags: ['docs', 'product'],
      });
    }

    if (metadata.docs?.faq) {
      docLinks.push({
        id: 'faq',
        title: 'Frequently Asked Questions',
        description: 'Find quick answers about licensing, onboarding timelines, and AI transparency.',
        href: metadata.docs.faq,
        category: 'support',
        tags: ['faq', 'support'],
      });
    }

    if (metadata.docs?.contact) {
      docLinks.push({
        id: 'contact-link',
        title: 'Email Support',
        description: 'Send us a detailed question or upload attachments directly to the support desk.',
        href: metadata.docs.contact,
        category: 'support',
        tags: ['contact'],
      });
    }

    return [...docLinks, ...staticArticles];
  }, [metadata]);

  const filteredArticles = useMemo(() => {
    if (!search.trim()) return augmentedArticles;
    const term = search.trim().toLowerCase();
    return augmentedArticles.filter((article) =>
      article.title.toLowerCase().includes(term) ||
      article.description.toLowerCase().includes(term) ||
      article.tags.some((tag) => tag.toLowerCase().includes(term))
    );
  }, [augmentedArticles, search]);

  const formulaEntries = useMemo(() => {
    const formulas = metadata.formulas ?? {};
    return Object.entries(formulas).map(([key, value]) => ({
      key,
      ...value,
    }));
  }, [metadata]);

  return (
    <div className="space-y-10">
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 relative overflow-hidden">
        <div className="absolute inset-y-0 right-0 w-64 bg-gradient-to-br from-primary-50 to-white pointer-events-none" aria-hidden="true" />
        <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="max-w-2xl">
            <h1 className="text-3xl font-bold text-gray-900">Help Center & Technical Library</h1>
            <p className="mt-3 text-base text-gray-600">
              Explore guided walkthroughs, accreditation playbooks, API references, and our technical whitepapers. Search the knowledge base or jump directly to the resources your team needs today.
            </p>
            {loading && (
              <p className="mt-4 text-sm text-primary-600">Loading latest documentation links…</p>
            )}
            {error && !loading && (
              <p className="mt-4 text-sm text-amber-600">{error}</p>
            )}
          </div>
          <div className="w-full md:w-80">
            <label className="relative block">
              <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-white py-3 pl-11 pr-4 text-sm text-gray-900 shadow-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
                placeholder="Search articles, formulas, or playbooks"
              />
            </label>
            <div className="mt-4 space-y-2 text-xs text-gray-500">
              <p className="font-medium uppercase tracking-wide text-gray-400">Popular queries</p>
              <div className="flex flex-wrap gap-2">
                {['coverage rate', 'api authentication', 'reviewer packs'].map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    className="rounded-full border border-primary-100 bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700 hover:bg-primary-100"
                    onClick={() => setSearch(chip)}
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        {[{
          title: 'Guided walkthroughs',
          description: 'Stepwise tutorials covering uploads, mapping standards, and generating reviewer packs.',
          icon: LifebuoyIcon,
        }, {
          title: 'Technical documentation',
          description: 'Architecture diagrams, API specs, and integration patterns for engineering teams.',
          icon: BookOpenIcon,
        }, {
          title: 'Whitepapers & research',
          description: 'Accreditation strategy playbooks, risk scoring methodology, and AI explainability briefs.',
          icon: DocumentTextIcon,
        }].map(({ title, description, icon: Icon }) => (
          <div key={title} className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-4">
              <span className="inline-flex rounded-xl bg-primary-50 p-3 text-primary-600">
                <Icon className="h-6 w-6" />
              </span>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
                <p className="mt-2 text-sm text-gray-600">{description}</p>
              </div>
            </div>
          </div>
        ))}
      </section>

      {formulaEntries.length > 0 && (
        <section className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900">Key Metrics & Formulas</h2>
          <p className="mt-2 text-sm text-gray-600">
            Reference the calculations that power your dashboard widgets and accreditation scorecards.
          </p>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {formulaEntries.map((formula) => (
              <div key={formula.key} className="rounded-lg border border-gray-100 bg-white/60 p-4 shadow-sm">
                <p className="text-sm font-semibold text-primary-700">{formula.label}</p>
                <p className="mt-1 text-xs uppercase tracking-wide text-gray-400">{formula.description}</p>
                {formula.formula && (
                  <p className="mt-3 rounded bg-primary-50 px-3 py-2 text-sm font-mono text-primary-900">{formula.formula}</p>
                )}
                {formula.range && (
                  <p className="mt-1 text-xs text-gray-500">Typical range: {formula.range}</p>
                )}
                {formula.aliases && formula.aliases.length > 0 && (
                  <p className="mt-3 text-xs text-gray-500">Also known as: {formula.aliases.join(', ')}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Knowledge Base</h2>
            <p className="mt-1 text-sm text-gray-600">
              Filter resources across implementation playbooks, technical documentation, and support guides.
            </p>
          </div>
          <p className="text-xs uppercase tracking-wide text-gray-400">{filteredArticles.length} resources</p>
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {filteredArticles.map((article) => (
            <a
              key={article.id}
              href={article.href}
              target={article.href.startsWith('http') ? '_blank' : undefined}
              rel={article.href.startsWith('http') ? 'noreferrer' : undefined}
              className="group flex flex-col justify-between rounded-lg border border-gray-100 bg-white/70 p-5 shadow-sm transition hover:border-primary-200 hover:shadow-md"
            >
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-primary-500">{article.category}</p>
                <h3 className="mt-2 text-lg font-semibold text-gray-900 group-hover:text-primary-700">
                  {article.title}
                </h3>
                <p className="mt-2 text-sm text-gray-600">{article.description}</p>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <div className="flex flex-wrap gap-2">
                  {article.tags.map((tag) => (
                    <span key={tag} className="rounded-full bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700">
                      {tag}
                    </span>
                  ))}
                </div>
                <ArrowTopRightOnSquareIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-600" />
              </div>
            </a>
          ))}
        </div>
        {filteredArticles.length === 0 && (
          <p className="mt-6 text-sm text-gray-500">
            No matches yet. Try searching for a different keyword or contact our team at{' '}
            <a href="mailto:support@mapmystandards.ai" className="text-primary-600 hover:text-primary-700">
              support@mapmystandards.ai
            </a>
            .
          </p>
        )}
      </section>

      <section className="rounded-xl border border-primary-100 bg-primary-50/60 p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">Need hands-on guidance?</p>
            <h2 className="text-2xl font-semibold text-primary-900">Schedule a working session with Customer Success</h2>
            <p className="mt-2 text-sm text-primary-800">
              We’ll pair you with an accreditation specialist to walk through evidence prep, reviewer workflows, or API integration use cases in real time.
            </p>
          </div>
          <div className="flex flex-col gap-3 md:w-80">
            <a
              href="https://calendly.com/mapmystandards/onboarding"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-700"
            >
              Book a session
            </a>
            <a
              href="mailto:support@mapmystandards.ai"
              className="inline-flex items-center justify-center rounded-lg border border-primary-200 bg-white px-4 py-2 text-sm font-semibold text-primary-700 shadow-sm transition hover:border-primary-300"
            >
              Email support
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HelpCenter;
