import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { requireOrgRole, auditLog } from '@/lib/rbac';
import { putObject } from '@/lib/storage/s3';
import pdfParse from 'pdf-parse';

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const contentType = req.headers.get('content-type') || '';
  if (!contentType.startsWith('multipart/form-data')) return NextResponse.json({ error: 'Expected multipart/form-data' }, { status: 400 });
  // @ts-ignore
  const form = await (req as any).formData();
  const file = form.get('file') as File | null;
  const orgId = form.get('orgId') as string | null;
  const title = form.get('title') as string | null;
  const documentId = form.get('documentId') as string | null;
  if (!file || !orgId) return NextResponse.json({ error: 'file and orgId required' }, { status: 400 });
  try { await requireOrgRole(session.user.email, orgId, 'CONTRIBUTOR'); } catch { return NextResponse.json({ error: 'Forbidden' }, { status: 403 }); }

  const user = await prisma.user.upsert({ where: { email: session.user.email }, update: {}, create: { email: session.user.email } });
  let docId = documentId;
  if (!docId) {
    if (!title) return NextResponse.json({ error: 'title required for new document' }, { status: 400 });
    const created = await prisma.document.create({ data: { orgId, title, mime: file.type, size: file.size, createdById: user.id } });
    docId = created.id;
  auditLog({ orgId, actorUserId: user.id, action: 'document.create', target: docId!, meta: { title, mime: file.type, size: file.size } });
  }

  const existingVersions = await prisma.documentVersion.count({ where: { documentId: docId } });
  const versionNumber = existingVersions + 1;
  const arrayBuffer = await file.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);
  const keyBase = `documents/${docId}/v${versionNumber}`;
  const objectKey = `${keyBase}/${file.name}`;
  await putObject(objectKey, buffer, file.type || 'application/octet-stream');

  const checksum = 'sha256:' + require('crypto').createHash('sha256').update(buffer).digest('hex');
  await prisma.documentVersion.create({ data: { documentId: docId, version: versionNumber, storageKey: objectKey, checksum, createdById: user.id } });

  let extractedText = '';
  if (file.type === 'application/pdf') {
    try { const parsed = await pdfParse(buffer); extractedText = parsed.text || ''; } catch (e) { console.warn('pdf parse failed', e); }
  }
  if (extractedText) {
    const dt = await prisma.documentText.create({ data: { documentId: docId, version: versionNumber, text: extractedText, lang: 'en' } });
    await prisma.$executeRawUnsafe(`UPDATE "DocumentText" SET "searchVector" = to_tsvector('english', $1) WHERE id = $2`, extractedText, dt.id);
  }
  auditLog({ orgId, actorUserId: user.id, action: 'document.upload', target: docId!, meta: { version: versionNumber, filename: file.name, bytes: file.size } });
  return NextResponse.json({ data: { documentId: docId, version: versionNumber } });
}
