import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  // @ts-ignore session injection via next-auth (placeholder)
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const user = await prisma.user.findUnique({ where: { email: session.user.email }, select: { id: true } });
  if (!user) return NextResponse.json({ data: null });
  const orgChart = await prisma.orgChart.findFirst({ where: { userId: user.id }, orderBy: { updatedAt: 'desc' } });
  return NextResponse.json({ data: orgChart });
}

export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json().catch(() => ({}));
  const { data } = body;
  if (!data) return NextResponse.json({ error: 'Missing data' }, { status: 400 });
  const user = await prisma.user.upsert({ where: { email: session.user.email }, update: {}, create: { email: session.user.email } });
  const saved = await prisma.orgChart.create({ data: { userId: user.id, data } });
  return NextResponse.json({ data: saved });
}

export const dynamic = 'force-dynamic';
