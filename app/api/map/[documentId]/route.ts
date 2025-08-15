import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(_req: Request, { params }: { params: { documentId: string } }) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const links = await prisma.evidenceLink.findMany({ where: { documentId: params.documentId }, orderBy: { confidence: 'desc' } });
  return NextResponse.json({ data: links });
}

export const dynamic = 'force-dynamic';
