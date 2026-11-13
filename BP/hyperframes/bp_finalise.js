// Blue Penguin - finalisation d'un rendu HyperFrames.
// Usage : node bp_finalise.js <rendu_hyperframes.mp4> <sortie_sans_extension> [seconde_miniature]
// Produit : <sortie>_son.mp4 (normalisé -16 LUFS, crête vraie < -4,5 dBFS), <sortie>.mp4 (muet),
//           <sortie>_720.gif (Slack / newsletter), <sortie>_miniature.jpg (couverture Reel).
// Puis mesure le son final (ebur128) et l'affiche : ne jamais dire « ça sonne bien » sans ces chiffres.
const cp = require('child_process'), fs = require('fs'), path = require('path');
const FFDIR = path.join(process.env.LOCALAPPDATA || '', 'Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin');
const ff = fs.existsSync(path.join(FFDIR, 'ffmpeg.exe')) ? path.join(FFDIR, 'ffmpeg.exe') : 'ffmpeg';
const [src, outBase, thumbAt] = process.argv.slice(2);
if (!src || !outBase) { console.log('usage: node bp_finalise.js rendu.mp4 sortie [seconde_miniature]'); process.exit(1); }
fs.mkdirSync(path.dirname(path.resolve(outBase)), { recursive: true });
const run = a => cp.execFileSync(ff, ['-y', '-loglevel', 'error', ...a]);
// 1. Son normalisé (2 passes loudnorm : mesure puis correction linéaire si possible)
const m = cp.spawnSync(ff, ['-i', src, '-af', 'loudnorm=I=-16:TP=-4.5:LRA=11:print_format=json', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
const j = JSON.parse(m.slice(m.lastIndexOf('{'), m.lastIndexOf('}') + 1));
run(['-i', src, '-c:v', 'copy', '-af', `loudnorm=I=-16:TP=-4.5:LRA=11:measured_I=${j.input_i}:measured_TP=${j.input_tp}:measured_LRA=${j.input_lra}:measured_thresh=${j.input_thresh}:offset=${j.target_offset},aresample=48000`, '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', outBase + '_son.mp4']);
// 2. Muet (LinkedIn, Stories avec musique Instagram)
run(['-i', src, '-c:v', 'copy', '-an', '-movflags', '+faststart', outBase + '.mp4']);
// 3. GIF 720 px
run(['-i', src, '-vf', 'fps=15,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=sierra2_4a', outBase + '_720.gif']);
// 4. Miniature (image finale lisible par défaut)
run([...(thumbAt ? ['-ss', thumbAt] : ['-sseof', '-0.2']), '-i', src, '-frames:v', '1', '-q:v', '3', outBase + '_miniature.jpg']);
// 5. Mesure du fichier exporté (stéréo et mono)
const meas = mono => { const e = cp.spawnSync(ff, ['-nostats', '-i', outBase + '_son.mp4', ...(mono ? ['-ac', '1'] : []), '-af', 'ebur128=peak=true', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const I = (e.match(/I:\s+(-?[\d.]+) LUFS/g) || []).pop(), P = (e.match(/Peak:\s+(-?[\d.]+) dBFS/g) || []).pop(); return `${I} · ${P}`; };
console.log('stéréo', meas(false)); console.log('mono  ', meas(true));
console.log('ok', ['_son.mp4', '.mp4', '_720.gif', '_miniature.jpg'].map(s => path.basename(outBase + s)).join(' + '));
