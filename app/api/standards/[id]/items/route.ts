import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const items = await prisma.standardItem.findMany({ where: { standardId: params.id }, orderBy: { path: 'asc' } });
  return NextResponse.json({ data: items });
}

export const dynamic = 'force-dynamic';
