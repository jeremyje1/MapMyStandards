// Authenticated UI smoke test for production using Playwright
// Env vars required:
//   MMS_BASE=https://platform.mapmystandards.ai (optional; defaults to prod)
//   MMS_API_KEY=... (optional; used for endpoints that accept X-API-Key)
//   MMS_JWT=... (optional; Bearer token placed in localStorage)

import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const BASE = process.env.MMS_BASE || 'https://platform.mapmystandards.ai';
const API_KEY = process.env.MMS_API_KEY || '';
const JWT = process.env.MMS_JWT || '';
const ART_DIR = path.resolve(process.cwd(), 'artifacts');

async function ensureDir(dir){
  await fs.promises.mkdir(dir, { recursive: true }).catch(()=>{});
}

function log(msg){
  process.stdout.write(`[SMOKE] ${msg}\n`);
}

async function run(){
  if (!API_KEY && !JWT) {
    console.error('Missing MMS_API_KEY or MMS_JWT env. Provide at least one.');
    process.exit(2);
  }

  await ensureDir(ART_DIR);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();

  // Inject tokens into localStorage before any page scripts run
  await page.addInitScript(({ apiKey, jwt }) => {
    try {
      if (apiKey) localStorage.setItem('a3e_api_key', apiKey);
      if (jwt) {
        localStorage.setItem('access_token', jwt);
        localStorage.setItem('jwt_token', jwt);
      }
    } catch {}
  }, { apiKey: API_KEY, jwt: JWT });

  // 1) Standards page loads
  log(`Navigating to ${BASE}/standards`);
  await page.goto(`${BASE}/standards`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(()=>{});
  log('Standards loaded');

  // 2) Evidence Mapping: Refresh Risk and wait for badges
  log(`Navigating to ${BASE}/evidence-mapping`);
  await page.goto(`${BASE}/evidence-mapping`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#btn-refresh-risk', { timeout: 15000 });
  await page.click('#btn-refresh-risk');
  await page.waitForSelector('#standardsList .risk-badge', { timeout: 30000 });
  await page.screenshot({ path: path.join(ART_DIR, 'evidence-mapping.png'), fullPage: true });
  log('Risk badges present on Evidence Mapping (screenshot saved)');

  // 3) Reports: Gap Analysis refresh, wait for chips and export CSV
  log(`Navigating to ${BASE}/reports`);
  await page.goto(`${BASE}/reports`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#btn-refresh-gap', { timeout: 15000 });
  await page.click('#btn-refresh-gap');
  await page.waitForSelector('#gapAnalysis .risk-chip', { timeout: 30000 });
  await page.screenshot({ path: path.join(ART_DIR, 'reports-gap.png'), fullPage: true });
  log('Gap Analysis chips present on Reports (screenshot saved)');

  // Click Export CSV and save download
  const [ download ] = await Promise.all([
    page.waitForEvent('download', { timeout: 30000 }),
    page.click('#btn-export-gaps')
  ]);
  const csvPath = path.join(ART_DIR, 'gap-analysis.csv');
  await download.saveAs(csvPath);
  log(`CSV exported: ${csvPath}`);

  await browser.close();
  log('Smoke test complete ✅');
}

run().catch(err => { console.error(err); process.exit(1); });
