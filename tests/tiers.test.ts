import { describe, it, expect } from 'vitest';
import { tierFromPriceId, TIERS } from '../lib/tiers';

describe('tiers definitions', () => {
  it('contains expected core tiers', () => {
    for (const key of ['department','campus','system','enterprise','pilot']) {
      expect(TIERS[key]).toBeTruthy();
    }
  });
});

describe('tierFromPriceId', () => {
  it('returns null when no env matches', () => {
    expect(tierFromPriceId('price_does_not_exist')).toBeNull();
  });
});
