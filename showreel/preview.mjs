// Render selected frames to PNG for review: node preview.mjs outdir f1 f2 ...
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import fs from 'fs'; import http from 'http'; import path from 'path';
const root = path.dirname(new URL(import.meta.url).pathname);
const srv = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.woff2') ? 'font/woff2' : 'application/octet-stream' }); r.end(d); }); }).listen(0);
const port = srv.address().port;
const [out, ...frames] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
p.on('console', m => console.log('[page]', m.text())); p.on('pageerror', e => console.log('[err]', e.message.slice(0, 3000)));
await p.goto(`http://localhost:${port}/reel.html`);
await p.evaluate(() => window.READY);
for (const f of frames.map(Number)) {
  const t0 = Date.now();
  const url = await p.evaluate(f => { renderFrame(f); return document.getElementById('c').toDataURL('image/png'); }, f);
  fs.writeFileSync(`${out}/f${String(f).padStart(4, '0')}.png`, Buffer.from(url.split(',')[1], 'base64'));
  console.log(f, Date.now() - t0, 'ms');
}
await b.close(); srv.close();
