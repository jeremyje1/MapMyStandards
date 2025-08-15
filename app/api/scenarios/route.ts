import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const scenarios = await prisma.scenario.findMany({ where: { user: { email: session.user.email } }, orderBy: { updatedAt: 'desc' } });
  return NextResponse.json({ data: scenarios });
}

export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json().catch(() => ({}));
  const { name, config } = body;
  if (!name || !config) return NextResponse.json({ error: 'Missing name or config' }, { status: 400 });
  const user = await prisma.user.upsert({ where: { email: session.user.email }, update: {}, create: { email: session.user.email } });
  const created = await prisma.scenario.create({ data: { userId: user.id, name, config } });
  return NextResponse.json({ data: created });
}

export const dynamic = 'force-dynamic';
