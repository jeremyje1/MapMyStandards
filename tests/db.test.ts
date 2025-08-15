import { describe, it, expect, beforeEach } from 'vitest';
import { upsertUserTier, getUserTier, listUserTiers, __clearMemoryStore } from '../lib/db';

describe('in-memory db tier store', () => {
  beforeEach(() => __clearMemoryStore());

  it('upserts and reads a tier', async () => {
    await upsertUserTier('a@example.com','campus');
    const rec = await getUserTier('a@example.com');
    expect(rec?.tier).toBe('campus');
  });

  it('lists tiers', async () => {
    await upsertUserTier('a@example.com','campus');
    await upsertUserTier('b@example.com','system');
    const list = await listUserTiers();
    expect(list.length).toBe(2);
  });
});
