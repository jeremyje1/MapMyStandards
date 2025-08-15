import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// POST /api/gaps/run?standardId=...&orgId=optional
export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { searchParams } = new URL(req.url);
  const standardId = searchParams.get('standardId');
  const orgId = searchParams.get('orgId') || undefined;
  if (!standardId) return NextResponse.json({ error: 'standardId required' }, { status: 400 });
  const standard = await prisma.standard.findUnique({ where: { id: standardId }, include: { items: true } });
  if (!standard) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  // Fetch evidence links for this standard (latest version only per document optionally)
  const links = await prisma.evidenceLink.findMany({ where: { standardId, status: { in: ['AUTO', 'CONFIRMED'] } } });
  const covered = new Set(links.map((l: any) => l.standardItemId));
  const missingItems = standard.items.filter((i: any) => !covered.has(i.id));
  const coveragePct = standard.items.length ? ( (standard.items.length - missingItems.length) / standard.items.length ) * 100 : 0;

  const result = {
    standardId,
    total: standard.items.length,
    covered: standard.items.length - missingItems.length,
  missing: missingItems.map((i: any) => ({ id: i.id, code: i.code, title: i.title })),
  };

  const run = await prisma.gapRun.create({ data: { standardId, orgId, coveragePct, missingCount: missingItems.length, totalCount: standard.items.length, resultJson: result } });
  return NextResponse.json({ data: { runId: run.id, coveragePct, missingCount: missingItems.length, totalCount: standard.items.length } });
}

export const dynamic = 'force-dynamic';
