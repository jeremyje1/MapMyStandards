// Central tier definitions & feature caps for MapMyStandards
// NOTE: Keep price IDs in env vars (do not hardcode live IDs here).

export interface TierFeatures {
  name: string;
  slug: string;
  annualPriceUSD?: number; // reference only; Stripe is source of truth
  standardSets: number | 'unlimited';
  artifactCap: number | 'unlimited';
  users: number | 'unlimited';
  aiNarratives: number | 'unlimited';
  connectors: boolean;
  sso: boolean;
  apiAccess: boolean;
  support: 'email' | 'priority' | 'premium';
  notes?: string;
}

export const TIERS: Record<string, TierFeatures> = {
  department: {
    name: 'Department (Self-Serve)',
    slug: 'department',
    annualPriceUSD: 9000,
    standardSets: 1,
    artifactCap: 500,
    users: 5,
    aiNarratives: 4,
    connectors: false,
    sso: false,
    apiAccess: false,
    support: 'email',
  },
  campus: {
    name: 'Campus (Team)',
    slug: 'campus',
    annualPriceUSD: 24000,
    standardSets: 3,
    artifactCap: 3000,
    users: 15,
    aiNarratives: 'unlimited',
    connectors: true,
    sso: false,
    apiAccess: false,
    support: 'email',
  },
  system: {
    name: 'System (Pro)',
    slug: 'system',
    annualPriceUSD: 48000,
    standardSets: 10,
    artifactCap: 'unlimited',
    users: 40,
    aiNarratives: 'unlimited',
    connectors: true,
    sso: true,
    apiAccess: true,
    support: 'priority',
  },
  enterprise: {
    name: 'Enterprise',
    slug: 'enterprise',
    annualPriceUSD: 75000,
    standardSets: 'unlimited',
    artifactCap: 'unlimited',
    users: 'unlimited',
    aiNarratives: 'unlimited',
    connectors: true,
    sso: true,
    apiAccess: true,
    support: 'premium',
    notes: 'Custom multi-campus; negotiated pricing.',
  },
  pilot: {
    name: 'Pilot (90 Day)',
    slug: 'pilot',
    annualPriceUSD: 4995,
    standardSets: 1,
    artifactCap: 250,
    users: 3,
    aiNarratives: 1,
    connectors: false,
    sso: false,
    apiAccess: false,
    support: 'email',
    notes: 'Time-boxed 90-day evaluation; convertible to annual plan.',
  },
};

export function tierFromPriceId(priceId?: string | null): string | null {
  if (!priceId) return null;
  const map: Record<string, string | undefined> = {
    [process.env.STRIPE_PRICE_DEPARTMENT_ANNUAL || '']: 'department',
    [process.env.STRIPE_PRICE_CAMPUS_ANNUAL || '']: 'campus',
    [process.env.STRIPE_PRICE_SYSTEM_ANNUAL || '']: 'system',
    [process.env.STRIPE_PRICE_PILOT || '']: 'pilot',
  };
  return map[priceId] || null;
}
