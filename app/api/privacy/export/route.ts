import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { requireOrgRole } from '@/lib/rbac';

export const dynamic = 'force-dynamic';

// GET /api/privacy/export?orgId=xyz
export async function GET(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { searchParams } = new URL(req.url);
  const orgId = searchParams.get('orgId') || '';
  if (!orgId) return NextResponse.json({ error: 'orgId required' }, { status: 400 });
  try { await requireOrgRole(session.user.email, orgId, 'OWNER'); } catch { return NextResponse.json({ error: 'Forbidden' }, { status: 403 }); }

  const [members, documents, standards] = await Promise.all([
    prisma.membership.findMany({ where: { orgId }, include: { user: true } }),
    prisma.document.findMany({ where: { orgId, isDeleted: false }, select: { id: true, title: true, mime: true, size: true, createdAt: true, updatedAt: true } }),
    prisma.evidenceLink.findMany({ where: { document: { orgId } }, select: { standardId: true }, distinct: ['standardId'] }),
  ]);

  const payload = {
    orgId,
    exportedAt: new Date().toISOString(),
    members: members.map((m: any) => ({ email: m.user.email, role: m.role })),
    documents,
    standards: standards.map((s: any) => s.standardId),
  };
  return NextResponse.json({ data: payload });
}
