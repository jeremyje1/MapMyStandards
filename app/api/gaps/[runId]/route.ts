import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(_req: Request, { params }: { params: { runId: string } }) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const run = await prisma.gapRun.findUnique({ where: { id: params.runId } });
  if (!run) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json({ data: run });
}

export const dynamic = 'force-dynamic';
