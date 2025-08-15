import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// GET /api/dashboard/trends?standardId=...&days=30
export async function GET(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { searchParams } = new URL(req.url);
  const standardId = searchParams.get('standardId');
  const days = parseInt(searchParams.get('days') || '30', 10);
  const since = new Date(Date.now() - days*24*60*60*1000);

  const where: any = { createdAt: { gte: since } };
  if (standardId) where.standardId = standardId;
  const links = await prisma.evidenceLink.findMany({ where });

  // Aggregate daily counts and confirmed rate
  const byDay: Record<string, { total: number; confirmed: number }> = {};
  for (const l of links as any[]) {
    const day = new Date(l.createdAt).toISOString().slice(0,10);
    if (!byDay[day]) byDay[day] = { total: 0, confirmed: 0 };
    byDay[day].total++;
    if (l.status === 'CONFIRMED') byDay[day].confirmed++;
  }

  const series = Object.keys(byDay).sort().map(d => ({ date: d, total: byDay[d].total, confirmed: byDay[d].confirmed, confirmationRate: byDay[d].total ? byDay[d].confirmed / byDay[d].total : 0 }));

  return NextResponse.json({ data: { series } });
}

export const dynamic = 'force-dynamic';
