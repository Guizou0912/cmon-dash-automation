// EXEMPLE MOTION (MP4 + GIF + version son) : « Chiffre clé » B2B, format feed 1080x1350.
// Un chiffre, une phrase, une source. Chiffre tiré du README Cas d'usage HCC (UC06) : bilan de saison, slide 10.
const path = require('path'), { pathToFileURL } = require('url');
const ph = f => pathToFileURL(path.join(__dirname, '../../assets/photos', f)).href;
const D = {
  kicker: 'Cas d’usage · le parcours fan',
  val: 99.6, dec: 1, suffix: ' %',
  line: 'des parcours vont jusqu’au <b>scan du billet</b> : 775 sur 778.',
  source: 'Source : Bilan de saison Blue Penguin × HCC 2025-2026, slide 10 (automations WELCOME et SCA)',
  photo: ph('2-programme-fidelite.jpg'),
};
module.exports = {
  format: 'motion', taille: 'feed', theme: 'navy', dur: 7,
  out: 'BP_CHIFFRE_EXEMPLE_99-6.mp4',
  photo: D.photo,
  scrim: 'linear-gradient(180deg,rgba(11,27,51,.96) 0%,rgba(11,27,51,.82) 38%,rgba(11,27,51,.25) 62%,rgba(11,27,51,.92) 100%)',
  css: `.fig{font-size:190px;margin-top:40px}.line{margin-top:22px}.bgphoto{object-position:50% 40%}`,
  body: `<div class="kicker" id="kicker">${D.kicker}</div><div class="rule" id="rule"></div>
<div class="fig" id="figw"><span id="fig">0</span></div>
<p class="line" id="line">${D.line}</p>
<div class="foot" id="foot"><div><p class="src">${D.source}</p><p class="url" style="margin-top:10px">bluepenguin.ch</p></div><span class="cta">Découvrir la solution</span></div>`,
  script: `function render(t){
  photo(t,7); intro(t);
  up('figw',t,0.8,0.6,40); count('fig',t,0.8,1.6,${D.val},${D.dec},'${D.suffix}');
  up('line',t,2.3,0.7); outro(t,3.2);
}`,
  // Palette son Blue Penguin : sobre, pas d'impact lourd (voir SKILL.md)
  sons: [[0.05, 'whoosh/fs393811.ogg', 0.5], [0.45, 'kit/click.ogg', 0.5], [0.8, 'riser/fs867126.ogg', 0.35, 1.6],
    ...[0, 1, 2, 3, 4, 5].map(k => [0.85 + k * 0.25, k % 2 ? 'tick/fs721514.ogg' : 'kit/tick.ogg', 0.35]),
    [2.4, 'ding/kenney-interface-confirmation-001.ogg', 0.6], [3.2, 'kit/whoosh.ogg', 0.45], [3.6, 'pop/fs527522.ogg', 0.6]],
};
