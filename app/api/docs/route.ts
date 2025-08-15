import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const spec = { openapi: '3.0.0', info: { title: 'MapMyStandards API', version: '0.1.0' }, paths: { '/api/health': { get: { summary: 'Health check' } }, '/api/documents': { get: { summary: 'List documents' }, post: { summary: 'Create document metadata' } }, '/api/upload': { post: { summary: 'Upload document version' } }, '/api/search': { get: { summary: 'Search documents' } }, '/api/standards': { get: { summary: 'List standards' } }, '/api/standards/import': { post: { summary: 'Import a standard' } }, '/api/map': { post: { summary: 'Auto map a document' } }, '/api/map/review': { post: { summary: 'Review evidence links' } }, '/api/gaps/run': { post: { summary: 'Run gap analysis' } }, '/api/gaps/{runId}': { get: { summary: 'Get gap run results' } }, '/api/narratives': { post: { summary: 'Generate narrative' } }, '/api/dashboard/summary': { get: { summary: 'Dashboard summary' } }, '/api/dashboard/trends': { get: { summary: 'Evidence trends' } }, '/api/privacy/export': { get: { summary: 'Export org data' } }, '/api/privacy/delete': { post: { summary: 'Delete org data' } }, '/api/stripe/webhook': { post: { summary: 'Stripe webhook' } } } };

export async function GET(req: Request) {
  const accept = req.headers.get('accept') || '';
  if (accept.includes('text/html')) return new NextResponse(`<html><body><h1>MapMyStandards API</h1><pre>${JSON.stringify(spec, null, 2)}</pre></body></html>`, { headers: { 'content-type': 'text/html' } });
  return NextResponse.json(spec);
}
