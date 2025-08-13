#!/usr/bin/env node
import { createCanvas, loadImage, registerFont } from 'canvas';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import path from 'path';

// Register a fallback font (system fonts may vary)
try { registerFont('/System/Library/Fonts/SFNS.ttf', { family: 'System' }); } catch {}

const OUT_DIR = path.join(process.cwd(), 'public', 'og');
if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });

const BRAND_GRADIENT = ['#1e3c72', '#2a5298'];
const FILES = [
  { file: 'accreditation-platform.jpg', title: 'AI Accreditation Platform', subtitle: 'Evidence • Analytics • Automation', badge: 'A³E Engine' },
  { file: 'a3e-dashboard.jpg', title: 'Live Accreditation Intelligence', subtitle: 'Predictive Gaps & Narrative Automation', badge: 'Dashboard' },
  { file: 'manual-cover.jpg', title: 'A³E User Manual', subtitle: 'Operational Guide & Best Practices', badge: 'Documentation' },
  { file: 'features.jpg', title: 'Platform Features', subtitle: 'Evidence Mapping • Gap Analytics • SSO', badge: 'Feature Stack' },
  { file: 'contact.jpg', title: 'Talk to Our Team', subtitle: 'Implementation & Enterprise Readiness', badge: 'Get in Touch' }
];

const WIDTH = 1200; const HEIGHT = 630;

function gradient(ctx) {
  const g = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT);
  BRAND_GRADIENT.forEach((c, i) => g.addColorStop(i, c));
  return g;
}

async function generate() {
  for (const spec of FILES) {
    const canvas = createCanvas(WIDTH, HEIGHT);
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = gradient(ctx);
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    // Overlay pattern
    ctx.globalAlpha = 0.15;
    ctx.fillStyle = '#ffffff';
    for (let i = 0; i < 140; i++) {
      const x = Math.random() * WIDTH;
      const y = Math.random() * HEIGHT;
      ctx.beginPath();
      ctx.arc(x, y, Math.random() * 3 + 1, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    // Badge
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    ctx.fillRect(60, 70, 380, 60);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 30px System, Helvetica, Arial';
    ctx.fillText(spec.badge.toUpperCase(), 80, 110);

    // Title
    ctx.fillStyle = '#ffffff';
    ctx.font = '700 70px System, Helvetica, Arial';
    wrapText(ctx, spec.title, 60, 230, WIDTH - 120, 78);

    // Subtitle
    ctx.font = '400 36px System, Helvetica, Arial';
    wrapText(ctx, spec.subtitle, 60, 400, WIDTH - 120, 46);

    // Footer brand
    ctx.font = '500 32px System, Helvetica, Arial';
    ctx.fillStyle = '#ffd166';
    ctx.fillText('MapMyStandards.ai', 60, HEIGHT - 80);
    ctx.fillStyle = '#ffffff';
    ctx.font = '400 24px System, Helvetica, Arial';
    ctx.fillText('AI-Powered Accreditation Intelligence', 60, HEIGHT - 40);

    const out = path.join(OUT_DIR, spec.file);
    writeFileSync(out, canvas.toBuffer('image/jpeg', { quality: 0.92 }));
    console.log('Generated', spec.file);
  }
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ');
  let line = '';
  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + ' ';
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && n > 0) {
      ctx.fillText(line, x, y);
      line = words[n] + ' ';
      y += lineHeight;
    } else {
      line = testLine;
    }
  }
  ctx.fillText(line.trim(), x, y);
}

generate().catch(e => { console.error(e); process.exit(1); });
