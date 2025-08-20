// Tier helpers for institutional pricing.

export type Tier = 'department' | 'campus' | 'system' | 'pilot';

const ids: Record<Tier, string> = {
  department: process.env.STRIPE_PRICE_DEPARTMENT_ANNUAL!,
  campus: process.env.STRIPE_PRICE_CAMPUS_ANNUAL!,
  system: process.env.STRIPE_PRICE_SYSTEM_ANNUAL!,
  pilot: process.env.STRIPE_PRICE_PILOT!,
};

export const priceIdFor = (tier: Tier): string => ids[tier];

export const tierFromPriceId = (priceId: string): Tier | null => {
  const entry = (Object.entries(ids) as [Tier, string][]).find(([, v]) => v === priceId);
  return entry ? entry[0] : null;
};
