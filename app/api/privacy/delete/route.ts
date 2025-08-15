import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { Prisma } from '@prisma/client';
import { requireOrgRole, auditLog } from '@/lib/rbac';

export const dynamic = 'force-dynamic';

// POST /api/privacy/delete { orgId }
// Performs a soft-delete of documents & records an audit trail.
export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json().catch(()=>({}));
  const { orgId } = body;
  if (!orgId) return NextResponse.json({ error: 'orgId required' }, { status: 400 });
  try { await requireOrgRole(session.user.email, orgId, 'OWNER'); } catch { return NextResponse.json({ error: 'Forbidden' }, { status: 403 }); }

  await prisma.$transaction(async (tx: Prisma.TransactionClient) => {
    await tx.document.updateMany({ where: { orgId }, data: { isDeleted: true } });
    await tx.auditLog.create({ data: { orgId, action: 'org.data_delete', target: orgId } });
  });

  auditLog({ orgId, action: 'privacy.delete', target: orgId });
  return NextResponse.json({ status: 'queued' });
}
