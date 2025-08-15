import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// POST /api/map  { documentId, version? }
// Simplified mapping: naive scoring by keyword overlap with standard item titles/description.
export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json().catch(() => ({}));
  const { documentId, version } = body;
  if (!documentId) return NextResponse.json({ error: 'documentId required' }, { status: 400 });
  const doc = await prisma.document.findUnique({ where: { id: documentId }, include: { texts: true } });
  if (!doc) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  const chosenVersion = version || doc.texts.sort((a: any,b: any)=>b.version-a.version)[0]?.version;
  if (!chosenVersion) return NextResponse.json({ error: 'No text' }, { status: 400 });
  const text = doc.texts.find((t: any)=>t.version===chosenVersion)?.text || '';

  // Fetch standards items (first standard only for demo)
  const firstStandard = await prisma.standard.findFirst({ include: { items: true }, orderBy: { updatedAt: 'desc' } });
  if (!firstStandard) return NextResponse.json({ data: [], note: 'No standards to map' });

  const lowerText = text.toLowerCase();
  const links: any[] = [];
  for (const item of firstStandard.items) {
    const key = item.code.toLowerCase();
    if (lowerText.includes(key)) {
      const idx = lowerText.indexOf(key);
      const snippet = text.slice(Math.max(0, idx-40), idx+key.length+40);
      links.push({ standardItemId: item.id, start: idx, end: idx+key.length, confidence: 0.4, method: 'keyword-code', rationale: snippet });
    }
  }

  // Insert EvidenceLinks (status AUTO)
  const created = [] as any[];
  for (const l of links) {
    const el = await prisma.evidenceLink.create({ data: { documentId, version: chosenVersion, standardId: firstStandard.id, standardItemId: l.standardItemId, start: l.start, end: l.end, confidence: l.confidence, method: l.method, rationale: l.rationale } });
    created.push(el);
  }
  return NextResponse.json({ data: created, mapped: created.length });
}

export const dynamic = 'force-dynamic';
