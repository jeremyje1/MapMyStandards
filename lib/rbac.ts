import { prisma } from '@/lib/prisma';
import type { Prisma } from '@prisma/client';
// Prisma enum types are not auto-exported as TS enums by default in this build context, using string union.
export type RoleString = 'OWNER' | 'CONTRIBUTOR' | 'VIEWER';
export type RequiredRole = RoleString | 'ANY_MEMBER';

export async function requireOrgRole(userEmail: string, orgId: string, minRole: RequiredRole): Promise<{ membershipId: string; role: RoleString; userId: string; }> {
  const user = await prisma.user.findUnique({ where: { email: userEmail }, include: { memberships: true } });
  if (!user) throw new Error('USER_NOT_FOUND');
  const membership = user.memberships.find((m: any) => m.orgId === orgId);
  if (!membership) throw new Error('NOT_MEMBER');
  if (minRole !== 'ANY_MEMBER' && !roleSatisfies(membership.role, minRole)) throw new Error('INSUFFICIENT_ROLE');
  return { membershipId: membership.id, role: membership.role, userId: user.id };
}

export function roleSatisfies(actual: RoleString, needed: RoleString): boolean {
  const order: RoleString[] = ['VIEWER','CONTRIBUTOR','OWNER'];
  return order.indexOf(actual) >= order.indexOf(needed);
}

export interface AuditLogParams {
  orgId: string;
  actorUserId?: string;
  action: string; // e.g. document.upload
  target?: string;
  meta?: Prisma.InputJsonValue;
}

export async function auditLog(p: AuditLogParams) {
  try {
    await prisma.auditLog.create({ data: { orgId: p.orgId, actorId: p.actorUserId, action: p.action, target: p.target, meta: p.meta } });
  } catch (e) {
    console.warn('Failed to write audit log', p.action, e);
  }
}
