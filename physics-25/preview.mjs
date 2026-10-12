// Render chosen moments to PNG for review: node preview.mjs outdir 1.5 20 33.2 ...   (seconds)
import fs from 'fs'; import { openPage } from './serve.mjs';
const [out, ...secs] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const { grab, close } = await openPage();
for (const s of secs.map(Number)) fs.writeFileSync(`${out}/t${s.toFixed(2).padStart(6, '0')}.png`, await grab(Math.round(s * 60)));
await close();
