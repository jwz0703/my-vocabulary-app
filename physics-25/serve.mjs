// Shared: static server + headless Chromium page with anim.html loaded.
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import fs from 'fs'; import http from 'http'; import path from 'path';
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.html': 'text/html', '.woff2': 'font/woff2' };
export async function openPage() {
  const srv = http.createServer((q, r) => {
    const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
    fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
  }).listen(0);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('console', m => console.log('[page]', m.text())); p.on('pageerror', e => console.log('[err]', e.message.slice(0, 3000)));
  await p.goto(`http://localhost:${srv.address().port}/anim.html`);
  await p.evaluate(() => window.READY);
  const grab = (f, type = 'image/png') => p.evaluate(([f, type]) => { renderFrame(f); return document.getElementById('c').toDataURL(type, .95); }, [f, type])
    .then(u => Buffer.from(u.split(',')[1], 'base64'));
  return { p, grab, close: async () => { await b.close(); srv.close(); } };
}
