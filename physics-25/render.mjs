// Render every frame to an H.264 video and dump the sound cues: node render.mjs video.mp4 cues.json
import fs from 'fs'; import { spawn } from 'child_process'; import { openPage } from './serve.mjs';
const [out, cuesOut] = process.argv.slice(2);
const { p, grab, close } = await openPage();
const { cues, dur, fps } = await p.evaluate(() => ({ cues: window.CUES, dur: window.DUR, fps: window.FPS }));
fs.writeFileSync(cuesOut, JSON.stringify({ dur, cues }));
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
const n = Math.round(dur * fps), t0 = Date.now();
for (let f = 0; f < n; f++) {
  const buf = await grab(f, 'image/jpeg');
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % 300 === 0) console.log(`frame ${f}/${n} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
ff.stdin.end(); await new Promise(r => ff.on('close', r));
await close(); console.log('done', ((Date.now() - t0) / 1000).toFixed(0), 's');
