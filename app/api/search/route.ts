import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// GET /api/search?q=...&type=document|text
export async function GET(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { searchParams } = new URL(req.url);
  const q = searchParams.get('q')?.trim();
  const type = searchParams.get('type') || 'document';
  if (!q) return NextResponse.json({ data: [] });

  // Basic membership: fetch user orgs (first pass; later enforce RBAC properly)
  const user = await prisma.user.findUnique({ where: { email: session.user.email }, include: { memberships: true } });
  if (!user) return NextResponse.json({ data: [] });
  const orgIds = user.memberships.map((m: typeof user.memberships[number]) => m.orgId);
  if (!orgIds.length) return NextResponse.json({ data: [] });

  // Use raw query for full-text ranking
  const results = await prisma.$queryRawUnsafe(`
    SELECT dt."documentId" as id, d.title, ts_headline('english', dt.text, plainto_tsquery('english', $1)) as snippet,
           ts_rank(dt."searchVector", plainto_tsquery('english', $1)) AS rank,
           dt.version
    FROM "DocumentText" dt
    JOIN "Document" d ON d.id = dt."documentId"
    WHERE d."orgId" = ANY($2::text[])
      AND dt."searchVector" @@ plainto_tsquery('english', $1)
    ORDER BY rank DESC
    LIMIT 50;
  `, q, orgIds);

  if (type === 'text') {
    return NextResponse.json({ data: results });
  }
  // Collapse to documents (best rank per doc)
  const docMap: Record<string, any> = {};
  for (const r of results as any[]) {
    if (!docMap[r.id]) docMap[r.id] = r;
  }
  return NextResponse.json({ data: Object.values(docMap) });
}

export const dynamic = 'force-dynamic';
