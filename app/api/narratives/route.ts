import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { putObject } from '@/lib/storage/s3';

// POST /api/narratives { standardsId, scope, includeEvidence, tone, audience }
// Simplified synchronous generation; in production convert to background job with polling.
export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json().catch(()=>null);
  if (!body) return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  const { standardsId, scope, includeEvidence = true, tone = 'professional', audience = 'accreditor' } = body;
  if (!standardsId) return NextResponse.json({ error: 'standardsId required' }, { status: 400 });

  const standard = await prisma.standard.findUnique({ where: { id: standardsId }, include: { items: { orderBy: { path: 'asc' } } } });
  if (!standard) return NextResponse.json({ error: 'Standard not found' }, { status: 404 });

  // Fetch evidence links (confirmed preferred fallback auto)
  const links = includeEvidence ? await prisma.evidenceLink.findMany({ where: { standardId: standardsId }, orderBy: { confidence: 'desc' } }) : [];
  const linksByItem = new Map<string, any[]>();
  for (const l of links) {
    if (!linksByItem.has(l.standardItemId)) linksByItem.set(l.standardItemId, []);
    linksByItem.get(l.standardItemId)!.push(l);
  }

  // Simple narrative assembly (placeholder for AI LLM generation)
  const lines: string[] = [];
  lines.push(`# Narrative Report: ${standard.name}`);
  if (standard.version) lines.push(`Version: ${standard.version}`);
  lines.push(`Tone: ${tone}; Audience: ${audience}`);
  lines.push('');
  for (const item of standard.items) {
    lines.push(`## ${item.code} ${item.title}`);
    if (includeEvidence) {
      const itemLinks = linksByItem.get(item.id) || [];
      if (itemLinks.length) {
        lines.push(`Evidence references (${itemLinks.length}):`);
        for (const el of itemLinks.slice(0,5)) {
          lines.push(`- Evidence (conf ${el.confidence.toFixed(2)}) doc:${el.documentId} v${el.version} span[${el.start}-${el.end}]`);
        }
      } else {
        lines.push('*No mapped evidence yet.*');
      }
    }
    lines.push('');
  }
  const markdown = lines.join('\n');

  // Convert to simple text for .docx placeholder (real DOCX via a library like docx npm) and PDF maybe via external service.
  const txtBuffer = Buffer.from(markdown, 'utf-8');
  const pdfBuffer = txtBuffer; // placeholder (store same) - replace with real PDF generation

  const run = await prisma.narrativeRun.create({ data: { standardId: standardsId, status: 'GENERATING', params: { scope, includeEvidence, tone, audience } } });
  const baseKey = `narratives/${standardsId}/${run.id}`;
  await putObject(baseKey + '.md', txtBuffer, 'text/markdown');
  await putObject(baseKey + '.pdf', pdfBuffer, 'application/pdf');
  await putObject(baseKey + '.docx', txtBuffer, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');

  await prisma.narrativeRun.update({ where: { id: run.id }, data: { status: 'COMPLETE', progress: 100, pdfKey: baseKey + '.pdf', docxKey: baseKey + '.docx' } });

  // Construct simple download URL (assumes public bucket or signed URL path handled elsewhere)
  return NextResponse.json({ data: { runId: run.id, pdfKey: baseKey + '.pdf', docxKey: baseKey + '.docx' } });
}

export const dynamic = 'force-dynamic';
