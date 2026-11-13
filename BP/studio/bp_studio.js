// Blue Penguin - studio de visuels (PNG fixe ou motion MP4 + GIF + version son).
// Séparé de GriddyPicks : charte, polices, sons et dossiers propres à Blue Penguin.
// Usage : node bp_studio.js chemin/post.js
// post.js exporte { format:'png'|'motion', taille:'feed'|'carre'|'story'|'linkedin', theme:'navy'|'blanc',
//   out, dur, css, body, script, sons:[[t,'dossier/fichier.ogg',volume,(duree)]], photo, scrim }
// Le script du post définit render(t) : chaque image est calculée -> export exact et reproductible.
const fs = require('fs'), path = require('path'), cp = require('child_process'), { pathToFileURL } = require('url');
const pw = require('playwright');
const POST = path.resolve(process.argv[2]);
const S = require(POST);
const DIR = path.dirname(POST);
const ROOT = path.resolve(__dirname, '..');
const A = f => pathToFileURL(path.join(ROOT, 'assets', f)).href;          // assets Blue Penguin
const FPS = 30;
const TAILLES = { feed: [1080, 1350], carre: [1080, 1080], story: [1080, 1920], linkedin: [1200, 627] };
const [W, H] = TAILLES[S.taille || 'feed'];
const NAVY = (S.theme || 'navy') === 'navy';

const fontFaces = (fam, pkg, weights) => weights.map(w => ['latin', 'latin-ext'].map(sub => {
  const f = path.join(__dirname, 'node_modules/@fontsource', pkg, 'files', `${pkg}-${sub}-${w}-normal.woff2`);
  return `@font-face{font-family:${fam};font-weight:${w};src:url('${pathToFileURL(f).href}')${sub === 'latin-ext' ? ';unicode-range:U+0100-024F' : ''}}`;
}).join('')).join('');
const faces = fontFaces('Outfit', 'outfit', [400, 500, 600, 700, 800]) + fontFaces('Inter', 'inter', [400, 500, 600, 700]);

// Charte Blue Penguin v1.0 (octobre 2026) — ne pas ajouter d'autre couleur.
const BASE_CSS = `
:root{--cyan:#40E4FC;--cyan2:#04CEEC;--cyan3:#0E9FBF;--ink:#14213D;--navy:#0B1B33;--muted:#5B6578;--n900:#262626;--white:#fff;--alt:#EEF1F6;
--bg:${NAVY ? 'var(--navy)' : 'var(--white)'};--fg:${NAVY ? '#fff' : 'var(--ink)'};--fg2:${NAVY ? 'rgba(255,255,255,.74)' : 'var(--muted)'};--display:Outfit}
*{box-sizing:border-box;margin:0;padding:0}
body{width:${W}px;height:${H}px;background:var(--bg);font-family:Inter,sans-serif;color:var(--fg);overflow:hidden}
.page{position:relative;width:${W}px;height:${H}px;padding:${S.taille === 'linkedin' ? '44px 56px' : '64px 64px 56px'};display:flex;flex-direction:column}
.bgphoto{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.scrim{position:absolute;inset:0;background:${S.scrim || 'linear-gradient(180deg,rgba(11,27,51,.92) 0%,rgba(11,27,51,.55) 45%,rgba(11,27,51,.15) 70%,rgba(11,27,51,.9) 100%)'}}

.logo{height:${S.taille === 'linkedin' ? 62 : 84}px}
.club{height:64px;object-fit:contain}
.kicker{position:relative;margin-top:44px;font:600 21px Inter;letter-spacing:.22em;text-transform:uppercase;color:var(--fg2)}
.rule{position:relative;width:76px;height:3px;background:var(--cyan);margin-top:16px;transform-origin:left}
h1{position:relative;font-family:var(--display);font-weight:500;letter-spacing:-1px;line-height:1.02;color:var(--fg)}
h1 .ln{display:block;overflow:hidden;padding:8px 0 4px;margin:-8px 0 -4px} h1 .in{display:inline-block}
.fig{position:relative;font-family:Inter;font-weight:600;letter-spacing:-.03em;line-height:1;color:${NAVY ? 'var(--cyan)' : 'var(--ink)'};font-variant-numeric:tabular-nums;white-space:nowrap}
.line{position:relative;font:400 30px/1.45 Inter;color:var(--fg2);max-width:860px}
.line b{color:var(--fg);font-weight:600}
.disc{position:relative;border-radius:50%;background:var(--cyan);color:var(--ink);display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Inter;font-weight:600;text-align:center}
.pill{display:inline-flex;align-items:center;gap:10px;border-radius:99px;background:var(--cyan);color:var(--ink);font:600 22px Inter;padding:10px 22px}
.card{border-radius:16px;background:${NAVY ? 'rgba(255,255,255,.06)' : 'var(--alt)'};padding:28px}
.foot{position:relative;margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;gap:24px;padding-right:${S.club_logo ? 330 : 190}px}
.brand{position:absolute;right:${S.taille === 'linkedin' ? 56 : 64}px;bottom:${S.taille === 'linkedin' ? 40 : 52}px;display:flex;align-items:center;gap:22px;z-index:2}
.src{font:400 16px/1.4 Inter;font-style:italic;color:var(--fg2);max-width:640px}
.url{font:600 24px Inter;color:${NAVY ? 'var(--cyan)' : 'var(--ink)'}}
.cta{display:inline-flex;align-items:center;height:64px;padding:0 30px;border-radius:6px;background:var(--cyan);color:var(--ink);font:500 24px Inter;white-space:nowrap}`;

// Bibliothèque d'animation disponible dans render(t)
const JS_LIB = `
const $=id=>document.getElementById(id);
const cl=x=>Math.max(0,Math.min(1,x));
const p=(t,a,d)=>cl((t-a)/d);
const oC=x=>1-Math.pow(1-x,3);
const oQ=x=>1-Math.pow(1-x,5);
const oB=x=>{const c1=1.4,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)};
const set=(id,o,tr)=>{const e=$(id);if(!e)return;e.style.opacity=o;e.style.transform=tr||''};
const up=(id,t,a,d,dist)=>{const k=oC(p(t,a,d||.6));set(id,k,'translateY('+((1-k)*(dist||24))+'px)')};
const mask=(id,t,a,d)=>{const k=oQ(p(t,a,d||.7));set(id,1,'translateY('+((1-k)*110)+'%)')};
const count=(id,t,a,d,val,dec,suffix)=>{const k=oQ(p(t,a,d||1.2));const v=val*k;
  $(id).textContent=v.toFixed(dec||0).replace('.',',').replace(/\\B(?=(\\d{3})+(?!\\d))/g,'\\u202f')+(suffix||'')};
const photo=(t,dur)=>{const e=$('bgphoto');if(e)e.style.transform='scale('+(1.08-0.08*oC(p(t,0,dur)))+')'};
function intro(t){ up('brand',t,0.1,0.6,16); up('kicker',t,0.35,0.5);
  const r=$('rule'); if(r) r.style.transform='scaleX('+oC(p(t,0.5,0.6))+')'; }
function outro(t,s){ up('foot',t,s,0.6,30); }`;

// Charte §6 : logo Blue Penguin en bas à droite ; logo du club à côté (à sa gauche), jamais à sa place.
const top = `<div class="brand" id="brand">${S.club_logo ? `<img class="club" id="club" src="${S.club_logo}">` : ''}<img class="logo" id="logo" src="${A(S.logo || 'logo_cyan.png')}"></div>`;
const html = `<!doctype html><html><head><meta charset="utf-8"><style>${faces}${BASE_CSS}${S.css || ''}</style></head><body><div class="page">
${S.photo ? `<img class="bgphoto" id="bgphoto" src="${S.photo}"><div class="scrim"></div>` : ''}
${S.sans_entete ? '' : top}
${S.body}
</div><script>${JS_LIB}const ASSET=${JSON.stringify(Object.fromEntries(fs.readdirSync(path.join(ROOT, 'assets')).filter(f => /\.(png|jpe?g)$/i.test(f)).map(f => [f, A(f)])))};
${S.script || 'function render(t){}'}
render(0);</script></body></html>`;

function ffmpegBin() {
  for (const c of [process.env.FFMPEG, 'ffmpeg'].filter(Boolean)) { try { cp.execFileSync(c, ['-version'], { stdio: 'ignore' }); return c; } catch (e) {} }
  for (const py of ['python', 'python3']) { try { return cp.execFileSync(py, ['-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())']).toString().trim(); } catch (e) {} }
  return null;
}

// Mixage des bruitages (port de mix_sons.py) : chaque son posé à son temps, puis loudnorm -16 LUFS, crête -4,5 dBFS.
function mixSons(ff, video, out, cues, dur) {
  const SFX = path.join(ROOT, 'sound-kit', 'sfx');
  const args = ['-y', '-loglevel', 'error', '-i', video]; const f = [];
  cues.forEach((c, i) => {
    const [t, snd, vol, md] = c; args.push('-i', path.join(SFX, snd));
    const ms = Math.round(Math.max(0, t) * 1000);
    const tr = md ? `,atrim=0:${md},afade=t=out:st=${Math.max(0, md - 0.25)}:d=0.25` : '';
    f.push(`[${i + 1}:a]aformat=sample_rates=48000:channel_layouts=stereo${tr},volume=${vol},adelay=${ms}|${ms}[a${i}]`);
  });
  f.push(cues.map((_, i) => `[a${i}]`).join('') + `amix=inputs=${cues.length}:normalize=0:dropout_transition=0,atrim=0:${dur},apad=whole_dur=${dur},loudnorm=I=-16:TP=-4.5:LRA=11[aout]`);
  args.push('-filter_complex', f.join(';'), '-map', '0:v', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out);
  cp.execFileSync(ff, args);
}

(async () => {
  const tmp = path.join(DIR, '_bp_studio.html'); fs.writeFileSync(tmp, html);
  const b = await pw.chromium.launch({ executablePath: process.env.BP_CHROMIUM || undefined });
  const png = S.format === 'png';
  const OUT = path.resolve(DIR, S.out), BASE = OUT.replace(/\.(png|mp4)$/, '');
  const pg = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: png ? 2 : 1 });
  await pg.goto(pathToFileURL(tmp).href); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(800);
  const bad = await pg.evaluate(() => [...document.images].filter(i => !i.naturalWidth).map(i => i.src));
  const font = await pg.evaluate(async () => { await document.fonts.load('500 40px Outfit'); await document.fonts.load('400 20px Inter'); return document.fonts.check('500 40px Outfit') && document.fonts.check('400 20px Inter'); });
  const dur = S.dur || 8;
  await pg.evaluate(t => render(t), dur);
  // contrôles automatiques : débordement, texte de plus de 6 mots dans le titre
  const over = await pg.evaluate(W => [...document.querySelectorAll('h1 .in,.fig,.line,.kicker,.cta,.pill,.src')]
    .filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > W - 40).map(e => e.textContent.trim().slice(0, 60)), W);
  const mots = await pg.evaluate(() => { const h = document.querySelector('h1'); return h ? h.textContent.trim().split(/\s+/).filter(w => /\w/.test(w)).length : 0; });
  await pg.screenshot({ path: png ? OUT : BASE + '_miniature.png' });
  if (!png) {
    const ff = ffmpegBin();
    if (!ff) { console.log('FFMPEG ABSENT'); await b.close(); process.exit(2); }
    const fr = path.join(DIR, '_frames'); fs.rmSync(fr, { recursive: true, force: true }); fs.mkdirSync(fr);
    const n = Math.round(FPS * dur);
    for (let i = 0; i < n; i++) { await pg.evaluate(t => render(t), i / FPS); await pg.screenshot({ path: path.join(fr, `f${String(i).padStart(4, '0')}.png`) }); }
    cp.execFileSync(ff, ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(fr, 'f%04d.png'),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT]);
    cp.execFileSync(ff, ['-y', '-loglevel', 'error', '-i', OUT, '-vf', 'fps=15,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=sierra2_4a', BASE + '_720.gif']);
    cp.execFileSync(ff, ['-y', '-loglevel', 'error', '-i', BASE + '_miniature.png', '-q:v', '3', BASE + '_miniature.jpg']); fs.rmSync(BASE + '_miniature.png');
    if (S.sons && S.sons.length) mixSons(ff, OUT, BASE + '_son.mp4', S.sons, dur);
    fs.rmSync(fr, { recursive: true, force: true });
  }
  await b.close(); fs.rmSync(tmp, { force: true });
  if (!font) console.log('POLICES OUTFIT/INTER NON CHARGEES');
  if (bad.length) console.log('IMAGES NON CHARGEES:', bad.join(' | '));
  if (over.length) console.log('TEXTE TROP LONG:', over.join(' | '));
  if (mots > 6) console.log(`TITRE TROP LONG : ${mots} mots (charte : 6 max)`);
  console.log('ok', OUT, png ? '' : `+ _720.gif + _miniature.jpg${S.sons && S.sons.length ? ' + _son.mp4' : ''}`);
})();
