import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

/* Expected JSON body shape:
{
  key: string,
  name: string,
  version?: string,
  publisher?: string,
  nodes: [ { code, title, description?, parentCode? } ... ]
}
parentCode omitted for root nodes. We'll derive hierarchy, level, path.
*/

export async function POST(req: Request) {
  // @ts-ignore
  const session = await (global as any).auth?.();
  if (!session?.user?.email) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json().catch(() => null);
  if (!body) return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  const { key, name, version, publisher, nodes } = body;
  if (!key || !name || !Array.isArray(nodes) || !nodes.length) return NextResponse.json({ error: 'Missing fields' }, { status: 400 });

  // Upsert standard header
  const standard = await prisma.standard.upsert({
    where: { key },
    update: { name, version, publisher },
    create: { key, name, version, publisher },
  });

  // Build maps
  interface NodeInput { code: string; title: string; description?: string; parentCode?: string }
  const byCode = new Map<string, NodeInput>();
  for (const n of nodes as NodeInput[]) {
    if (!n.code || !n.title) return NextResponse.json({ error: 'Node missing code/title' }, { status: 400 });
    byCode.set(n.code, n);
  }

  // Prepare insertion preserving parent before child (simple multi-pass or recursion)
  const createdIdByCode = new Map<string, string>();
  const pending = Array.from(byCode.values());
  const toCreate: any[] = [];

  function ensurePath(code: string, stack: string[] = []): { path: string; level: number; parentCode?: string } {
    const node = byCode.get(code);
    if (!node) throw new Error('Missing node for code ' + code);
    if (!node.parentCode) return { path: code, level: 0 };
    if (stack.includes(code)) throw new Error('Cycle detected at ' + code);
    const parentInfo = ensurePath(node.parentCode, stack.concat(code));
    return { path: parentInfo.path + '/' + code, level: parentInfo.level + 1, parentCode: node.parentCode };
  }

  for (const node of pending) {
    const { path, level, parentCode } = ensurePath(node.code);
    toCreate.push({ ...node, path, level, parentCode });
  }

  // Delete existing items (simplest approach for re-import)
  await prisma.standardItem.deleteMany({ where: { standardId: standard.id } });

  // Insert in parent-first order
  toCreate.sort((a, b) => a.level - b.level);

  const createdItems: { code: string; id: string }[] = [];
  for (const n of toCreate) {
    const parentId = n.parentCode ? createdItems.find(ci => ci.code === n.parentCode)?.id : null;
    const item = await prisma.standardItem.create({ data: { standardId: standard.id, code: n.code, title: n.title, description: n.description, parentId, level: n.level, path: n.path } });
    createdItems.push({ code: n.code, id: item.id });
  }

  return NextResponse.json({ data: { standardId: standard.id, count: createdItems.length } });
}

export const dynamic = 'force-dynamic';
