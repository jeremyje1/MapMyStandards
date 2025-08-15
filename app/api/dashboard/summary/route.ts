import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// GET /api/dashboard/summary?standardId=...&orgId=...
export async function GET(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { searchParams } = new URL(req.url);
  const standardId = searchParams.get('standardId');
  const orgId = searchParams.get('orgId') || undefined;

  const filters: any = {};
  if (standardId) filters.id = standardId;
  const standard = await prisma.standard.findFirst({ where: filters, include: { items: true } });
  const totalItems = standard ? standard.items.length : 0;

  const evidenceWhere: any = {};
  if (standardId) evidenceWhere.standardId = standardId;
  if (orgId) {
    // restrict documents to org
    const orgDocIds = await prisma.document.findMany({ where: { orgId }, select: { id: true } });
  evidenceWhere.documentId = { in: orgDocIds.map((d: any) => d.id) };
  }
  const evidenceLinks = await prisma.evidenceLink.findMany({ where: evidenceWhere });
  const mappedItems = new Set(evidenceLinks.map((l: any) => l.standardItemId));

  // Coverage
  const coveragePct = totalItems ? (mappedItems.size / totalItems) * 100 : 0;

  // Gaps by level (only if standard)
  const gapsByLevel: Record<number, { missing: number; total: number }> = {};
  if (standard) {
    for (const item of standard.items) {
      if (!gapsByLevel[item.level]) gapsByLevel[item.level] = { missing: 0, total: 0 };
      gapsByLevel[item.level].total++;
      if (!mappedItems.has(item.id)) gapsByLevel[item.level].missing++;
    }
  }

  // Stale evidence: links older than 30 days relative to latest document version
  const staleThreshold = Date.now() - 1000*60*60*24*30;
  const stale = evidenceLinks.filter((l: any) => new Date(l.updatedAt).getTime() < staleThreshold).length;

  const docsCount = await prisma.document.count();
  const autoCount = evidenceLinks.filter((l: any) => l.status === 'AUTO').length;
  const confirmedCount = evidenceLinks.filter((l: any) => l.status === 'CONFIRMED').length;

  return NextResponse.json({
    data: {
      coveragePct,
      totalItems,
      mappedItems: mappedItems.size,
      docs: docsCount,
      evidence: evidenceLinks.length,
      auto: autoCount,
      confirmed: confirmedCount,
      stale,
      gapsByLevel
    }
  });
}

export const dynamic = 'force-dynamic';
