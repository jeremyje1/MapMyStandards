import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export const dynamic = 'force-dynamic';

export async function GET() {
  const checks: Record<string, any> = {};
  try { await prisma.$queryRawUnsafe('SELECT 1'); checks.db = 'ok'; } catch (e: any) { checks.db = 'fail:' + e.message; }
  checks.time = new Date().toISOString();
  return NextResponse.json({ status: Object.values(checks).every(v => v === 'ok') ? 'ok' : 'degraded', checks });
}
