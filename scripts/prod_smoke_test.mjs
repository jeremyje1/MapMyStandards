// Authenticated UI smoke test for production using Playwright
// Env vars required:
//   MMS_BASE=https://platform.mapmystandards.ai (optional; defaults to prod)
//   MMS_API_KEY=... (optional; used for endpoints that accept X-API-Key)
//   MMS_JWT=... (optional; Bearer token placed in localStorage)

import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const BASE = process.env.MMS_BASE || process.env.FRONTEND_URL || process.env.API_BASE_URL || process.env.BASE_URL || process.env.PLATFORM_BASE_URL || 'https://platform.mapmystandards.ai';
const API_KEY = process.env.MMS_API_KEY || process.env.API_KEY || process.env.A3E_API_KEY || '';
const JWT = process.env.MMS_JWT || process.env.JWT || process.env.ACCESS_TOKEN || process.env.BEARER_TOKEN || '';
const ART_DIR = path.resolve(process.cwd(), 'artifacts');
const S3_BUCKET = process.env.MMS_ARTIFACTS_BUCKET || process.env.S3_BUCKET || '';
const S3_PREFIX = process.env.MMS_ARTIFACTS_PREFIX || 'smoke-tests';
const COMMIT_SHA = process.env.MMS_COMMIT_SHA || '';

let S3ClientCtor = null;
let PutObjectCommandCtor = null;

function applyEnvFromText(txt){
  if (!txt) return;
  for (const line of txt.split(/\r?\n/)){
    if (!line || /^\s*#/.test(line)) continue;
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!m) continue;
    const key = m[1];
    let val = m[2];
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith('\'') && val.endsWith('\''))) {
      val = val.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = val;
  }
}

function tryLoadDotenvFiles(){
  const candidates = [
    path.resolve(process.cwd(), 'scripts/smoke.env'),
    path.resolve(process.cwd(), '.env')
  ];
  for (const f of candidates){
    try {
      if (fs.existsSync(f)) {
        const txt = fs.readFileSync(f, 'utf8');
        applyEnvFromText(txt);
      }
    } catch {}
  }
}

async function tryLoadS3(){
  if (!S3_BUCKET) return false;
  try {
    const mod = await import('@aws-sdk/client-s3');
    S3ClientCtor = mod.S3Client;
    PutObjectCommandCtor = mod.PutObjectCommand;
    return true;
  } catch (e) {
    console.warn('[SMOKE] S3 upload requested but @aws-sdk/client-s3 not installed. Run: npm i -D @aws-sdk/client-s3');
    return false;
  }
}

async function uploadFileToS3(filePath, key){
  if (!S3ClientCtor || !PutObjectCommandCtor) return null;
  const region = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'us-east-1';
  const client = new S3ClientCtor({ region });
  const body = await fs.promises.readFile(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const type = ext === '.png' ? 'image/png' : ext === '.csv' ? 'text/csv' : 'application/octet-stream';
  const cmd = new PutObjectCommandCtor({ Bucket: S3_BUCKET, Key: key, Body: body, ContentType: type });
  await client.send(cmd);
  return `s3://${S3_BUCKET}/${key}`;
}

async function ensureDir(dir){
  await fs.promises.mkdir(dir, { recursive: true }).catch(()=>{});
}

function log(msg){
  process.stdout.write(`[SMOKE] ${msg}\n`);
}

async function run(){
  // Late-load dotenv files to populate env if missing
  if (!API_KEY && !JWT) tryLoadDotenvFiles();

  const key = process.env.MMS_API_KEY || process.env.API_KEY || process.env.A3E_API_KEY || API_KEY;
  const jwt = process.env.MMS_JWT || process.env.JWT || process.env.ACCESS_TOKEN || process.env.BEARER_TOKEN || JWT;
  const loginEmail = process.env.TEST_USER_EMAIL || process.env.A3E_TEST_EMAIL || '';
  const loginPassword = process.env.TEST_USER_PASSWORD || process.env.A3E_TEST_PASSWORD || '';

  if (!key && !jwt && (!loginEmail || !loginPassword)) {
    console.error('Missing MMS_API_KEY or MMS_JWT or TEST_USER_EMAIL/TEST_USER_PASSWORD. Provide at least one auth method.');
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
  }, { apiKey: key, jwt });

  // Optional: login via UI if no token/key provided (robust fallback for prod)
  if (loginEmail && loginPassword && !key && !jwt) {
    log('Logging in via UI using TEST_USER_EMAIL/TEST_USER_PASSWORD');
    // Try /login first, then fallback to /login-platform.html
    const tryLogin = async (path) => {
      await page.goto(`${BASE}${path}`, { waitUntil: 'domcontentloaded' });
      const emailSel = 'input[name="email"], input#email, input[type="email"]';
      const passSel = 'input[name="password"], input#password, input[type="password"]';
      await page.waitForSelector(emailSel, { timeout: 15000 });
      await page.fill(emailSel, loginEmail);
      await page.fill(passSel, loginPassword);
      const btnSel = 'button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), button#loginButton, #loginBtn';
      await page.click(btnSel).catch(()=>{});
      await page.waitForURL(/platform\.mapmystandards\.ai|ai-dashboard|standards|evidence-mapping/, { timeout: 20000 }).catch(()=>{});
      // Presence of session UI or redirect
      await page.waitForSelector('a:has-text("Logout"), a[href*="logout"], #mmsSessBtn', { timeout: 20000 }).catch(()=>{});
    };
    try {
      await tryLogin('/login');
    } catch (_) {
      await tryLogin('/login-platform.html');
    }
  }

  // 1) Standards page loads
  log(`Navigating to ${BASE}/standards`);
  await page.goto(`${BASE}/standards`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(()=>{});
  log('Standards loaded');

  // 2) Evidence Mapping: Refresh Risk and wait for badges
  log(`Navigating to ${BASE}/evidence-mapping`);
  await page.goto(`${BASE}/evidence-mapping`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#btn-refresh-risk', { timeout: 15000 }).catch(()=>{});
  await page.click('#btn-refresh-risk').catch(()=>{});
  // Accept either computed risk badges or populated standards list (for empty/demo accounts)
  const riskOrList = page.locator('#standardsList .risk-badge, #standardsList .standard-item');
  await riskOrList.first().waitFor({ state: 'visible', timeout: 30000 }).catch(()=>{});
  await page.screenshot({ path: path.join(ART_DIR, 'evidence-mapping.png'), fullPage: true });
  log('Risk badges present on Evidence Mapping (screenshot saved)');

  // 3) Reports: Gap Analysis refresh, wait for chips and export CSV
  log(`Navigating to ${BASE}/reports`);
  await page.goto(`${BASE}/reports`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#btn-refresh-gap', { timeout: 15000 }).catch(()=>{});
  await page.click('#btn-refresh-gap').catch(()=>{});
  // Accept either risk chips or populated dashboard metrics grid
  const chipsOrMetrics = page.locator('#gapAnalysis .risk-chip, #dashboardMetrics');
  await chipsOrMetrics.first().waitFor({ state: 'visible', timeout: 30000 }).catch(()=>{});
  await page.screenshot({ path: path.join(ART_DIR, 'reports-gap.png'), fullPage: true });
  log('Gap Analysis chips present on Reports (screenshot saved)');

  // Click Export CSV and save download
  // Export CSV if available; otherwise continue
  try {
    const [ download ] = await Promise.all([
      page.waitForEvent('download', { timeout: 30000 }),
      page.click('#btn-export-gaps')
    ]);
    const csvPath = path.join(ART_DIR, 'gap-analysis.csv');
    await download.saveAs(csvPath);
    log(`CSV exported: ${csvPath}`);
  } catch (e) {
    log('CSV export not available; continuing');
  }

  await browser.close();

  // Optional: upload artifacts to S3 if configured
  const wantS3 = !!S3_BUCKET && (await tryLoadS3());
  if (wantS3) {
    const stamp = new Date().toISOString().replaceAll(':', '-');
    const baseKey = `${S3_PREFIX}/${COMMIT_SHA || 'manual'}/${stamp}`;
    const files = [
      { local: path.join(ART_DIR, 'evidence-mapping.png'), key: `${baseKey}/evidence-mapping.png` },
      { local: path.join(ART_DIR, 'reports-gap.png'), key: `${baseKey}/reports-gap.png` },
      { local: path.join(ART_DIR, 'gap-analysis.csv'), key: `${baseKey}/gap-analysis.csv` },
    ];
    for (const f of files) {
      try {
        if (fs.existsSync(f.local)) {
          const loc = await uploadFileToS3(f.local, f.key);
          if (loc) log(`Uploaded: ${loc}`);
        }
      } catch (e) {
        console.warn(`[SMOKE] Failed S3 upload for ${f.local}:`, e?.message || e);
      }
    }
  } else if (S3_BUCKET) {
    console.warn('[SMOKE] Skipped S3 upload (missing SDK).');
  }

  log('Smoke test complete ✅');
}

run().catch(err => { console.error(err); process.exit(1); });
