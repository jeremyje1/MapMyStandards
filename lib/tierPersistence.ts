// Persistence helper for storing user tiers in the backend.

export async function persistUserTier({ email, tier, source }: { email: string; tier: string; source?: string }): Promise<void> {
  try {
    await fetch('https://api.mapmystandards.ai/api/tier/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, tier, source }),
      // No credentials; backend should validate via internal logic / future shared secret
    });
  } catch (err) {
    if (process.env.NODE_ENV !== 'production') {
      console.warn('persistUserTier error', err);
    }
  }
}
