import React from 'react';

async function fetchItems(id: string) {
  const base = process.env.NEXT_PUBLIC_APP_URL || '';
  const res = await fetch(`${base}/api/standards/${id}/items`, { cache: 'no-store' });
  const json = await res.json();
  return json.data || [];
}

function buildTree(items: any[]) {
  const byId: Record<string, any> = {};
  items.forEach(i => { byId[i.id] = { ...i, children: [] }; });
  const roots: any[] = [];
  items.forEach(i => {
    if (i.parentId) byId[i.parentId]?.children.push(byId[i.id]); else roots.push(byId[i.id]);
  });
  return roots;
}

function Tree({ nodes }: { nodes: any[] }) {
  return (
    <ul className="ml-4 list-disc">
      {nodes.map(n => (
        <li key={n.id} className="mb-1">
          <span className="font-medium">{n.code}</span>: {n.title}
          {n.children?.length ? <Tree nodes={n.children} /> : null}
        </li>
      ))}
    </ul>
  );
}

export default async function StandardDetail({ params }: { params: { id: string } }) {
  const items = await fetchItems(params.id);
  const tree = buildTree(items);
  return (
    <div className="max-w-5xl mx-auto p-6">
      <a href="/standards" className="text-sm text-blue-600 underline">&larr; Back</a>
      <h1 className="text-2xl font-bold mt-2 mb-4">Framework Structure</h1>
      <div className="bg-white border rounded p-4 shadow-sm">
        {tree.length ? <Tree nodes={tree} /> : <div className="text-sm text-gray-500">No items.</div>}
      </div>
    </div>
  );
}
