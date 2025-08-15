import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { auditLog, requireOrgRole } from '@/lib/rbac';

// POST /api/map/review { confirm: [ids], reject: [ids] }
export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json().catch(()=>({}));
  const { confirm = [], reject = [] } = body;
  const updates: any[] = [];
  // Derive org from first evidence link (simplistic; could accept orgId param)
  const firstLink = confirm[0] || reject[0];
  if (!firstLink) return NextResponse.json({ data: [] });
  const link = await prisma.evidenceLink.findUnique({ where: { id: firstLink }, include: { document: true } });
  if (!link) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  const orgId = link.document.orgId;
  try {
    await requireOrgRole(session.user.email, orgId, 'CONTRIBUTOR');
  } catch {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }
  let confirmed = 0; let rejected = 0;
  if (confirm.length) {
    const r = await prisma.evidenceLink.updateMany({ where: { id: { in: confirm } }, data: { status: 'CONFIRMED' } });
    confirmed = r.count;
    if (r.count) auditLog({ orgId, action: 'evidence.confirm', target: confirm.join(','), meta: { count: r.count } });
  }
  if (reject.length) {
    const r = await prisma.evidenceLink.updateMany({ where: { id: { in: reject } }, data: { status: 'REJECTED' } });
    rejected = r.count;
    if (r.count) auditLog({ orgId, action: 'evidence.reject', target: reject.join(','), meta: { count: r.count } });
  }
  updates.push({ confirmed, rejected });
  return NextResponse.json({ data: updates });
}

export const dynamic = 'force-dynamic';
