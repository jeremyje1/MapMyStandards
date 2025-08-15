// Lightweight DB client abstraction placeholder.
// Replace with Prisma/Drizzle implementation when schema defined.

export interface UserTierRecord {
  email: string;
  tier: string;
  updatedAt: Date;
  source?: string;
}

// In-memory store (non-persistent) as a temporary stand-in.
const memoryStore: Record<string, UserTierRecord> = {};

export async function upsertUserTier(email: string, tier: string, source?: string): Promise<UserTierRecord> {
  const record: UserTierRecord = { email, tier, updatedAt: new Date(), source };
  memoryStore[email] = record;
  return record;
}

export async function getUserTier(email: string): Promise<UserTierRecord | null> {
  return memoryStore[email] || null;
}

export async function listUserTiers(): Promise<UserTierRecord[]> {
  return Object.values(memoryStore);
}

export function __clearMemoryStore() { // test helper
  for (const k of Object.keys(memoryStore)) delete memoryStore[k];
}
