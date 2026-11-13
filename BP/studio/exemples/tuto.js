// EXEMPLE PNG : « Tuto fan » B2C Instagram, fond blanc + aplat cyan, tutoiement.
// Le disque cyan porte le chiffre clé (motif signature du logo). Titre <= 6 mots.
const path = require('path'), { pathToFileURL } = require('url');
const el = f => pathToFileURL(path.join(__dirname, '../../assets/elements', f)).href;
const STEPS = [
  { ico: 'icona_green_ticket.png', t: 'Scanne ton billet', n: '1' },
  { ico: 'icona_green_commerce.png', t: 'Achète à la boutique', n: '2' },
  { ico: 'icona_green_coment.png', t: 'Commente sur Instagram', n: '3' }];
// Les barèmes de points (+250 / +100 / +20 vus sur une maquette) ne sont PAS sourcés :
// on ne les affiche qu'une fois confirmés par le club ou le bilan de saison.
module.exports = {
  format: 'png', taille: 'feed', theme: 'blanc', logo: 'logo_navy.png', out: 'BP_TUTO_EXEMPLE_GAGNER-DES-POINTS.png',
  css: `
.band{position:absolute;left:0;right:0;bottom:0;height:250px;background:var(--cyan)}
h1{font-size:96px;margin-top:28px}
.steps{position:relative;margin-top:56px;display:flex;flex-direction:column;gap:18px}
.step{display:flex;align-items:center;gap:24px;background:#fff;border-radius:16px;padding:22px 28px;box-shadow:0 1px 0 rgba(20,33,61,.06)}
.step img{width:64px;height:64px}
.step .t{flex:1;font:500 34px Outfit;color:var(--ink)}
.step .disc{width:96px;height:96px;font-size:40px}
.step .disc small{font:500 15px Inter;letter-spacing:.06em;text-transform:uppercase}
.foot .url{color:var(--ink)}
.cta{background:var(--ink);color:#fff}`,
  body: `<div class="band"></div>
<div class="kicker" id="kicker">Tuto · tes points</div><div class="rule" id="rule"></div>
<h1><span class="ln"><span class="in">Chaque match</span></span><span class="ln"><span class="in">te rapporte.</span></span></h1>
<div class="steps">${STEPS.map(s => `<div class="step"><img src="${el(s.ico)}"><span class="t">${s.t}</span><div class="disc">${s.n}</div></div>`).join('')}</div>
<div class="foot"><span class="cta">Rejoins le programme</span><p class="url">bluepenguin.ch</p></div>`,
};
