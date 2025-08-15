import { prisma } from '@/lib/prisma';
import { Prisma } from '@prisma/client';

// Canonical tier string union (mirrors Prisma enum in schema)
export type TierString = 'department' | 'campus' | 'system' | 'enterprise' | 'pilot' | 'unknown';

// Helper: normalize arbitrary string to Tier enum (fallback to unknown)
function normalizeTier(t?: string | null): TierString | undefined {
  if (!t) return undefined;
  const lowered = t.toLowerCase();
  if ((['department','campus','system','enterprise','pilot','unknown'] as string[]).includes(lowered)) return lowered as TierString;
  return 'unknown';
}

export interface PersistUserTierParams {
  email: string;
  tier: string | null;
  source?: string; // stripe session / subscription id for traceability
  stripeCustomerId?: string | null;
  stripeSubscriptionId?: string | null;
  priceId?: string | null;
  priceEnvKey?: string | null;
  status?: string | null;
  currentPeriodEnd?: Date | null;
}

export async function persistUserTier(params: PersistUserTierParams) {
  const { email, tier, source, stripeCustomerId, stripeSubscriptionId, priceId, priceEnvKey, status, currentPeriodEnd } = params;
  return prisma.$transaction(async (tx: Prisma.TransactionClient) => {
    const user = await tx.user.upsert({
      where: { email },
      create: { email, tier: normalizeTier(tier) },
      update: { tier: normalizeTier(tier) }
    });

    if (stripeSubscriptionId || stripeCustomerId) {
      // Upsert subscription record by stripeSubscriptionId when available, else by (userId + priceId) pair
      if (stripeSubscriptionId) {
        await tx.subscription.upsert({
          where: { stripeSubscriptionId },
          create: {
            userId: user.id,
            stripeCustomerId: stripeCustomerId || undefined,
            stripeSubscriptionId,
            priceId: priceId || undefined,
            priceEnvKey: priceEnvKey || undefined,
            status: status || undefined,
            currentPeriodEnd: currentPeriodEnd || undefined,
          },
          update: {
            stripeCustomerId: stripeCustomerId || undefined,
            priceId: priceId || undefined,
            priceEnvKey: priceEnvKey || undefined,
            status: status || undefined,
            currentPeriodEnd: currentPeriodEnd || undefined,
          }
        });
      } else {
        // Fallback upsert by userId + priceId uniqueness assumption
        await tx.subscription.create({
          data: {
            userId: user.id,
            stripeCustomerId: stripeCustomerId || undefined,
            priceId: priceId || undefined,
            priceEnvKey: priceEnvKey || undefined,
            status: status || undefined,
            currentPeriodEnd: currentPeriodEnd || undefined,
          }
        });
      }
    }

    return { userId: user.id, source };
  });
}

export async function getUserTier(email: string): Promise<TierString | null> {
  const user = await prisma.user.findUnique({ where: { email }, select: { tier: true } });
  return (user?.tier as TierString) || null;
}
