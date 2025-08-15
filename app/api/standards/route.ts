import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const standards = await prisma.standard.findMany({ orderBy: { updatedAt: 'desc' } });
  return NextResponse.json({ data: standards });
}

export const dynamic = 'force-dynamic';
