// EXEMPLE PNG : visuel LinkedIn paysage 1200x627, B2B (clubs, partenaires, marques), vouvoiement.
// Chiffre tiré du README Cas d'usage HCC (UC07) : bilan de saison, slides 2 et 9.
const path = require('path'), { pathToFileURL } = require('url');
const ph = f => pathToFileURL(path.join(__dirname, '../../assets/photos', f)).href;
module.exports = {
  format: 'png', taille: 'linkedin', theme: 'navy', out: 'BP_LINKEDIN_EXEMPLE_62-8.png',
  photo: ph('6-integration-sso.jpg'),
  scrim: 'linear-gradient(90deg,rgba(11,27,51,.97) 0%,rgba(11,27,51,.9) 46%,rgba(11,27,51,.2) 75%,rgba(11,27,51,.1) 100%)',
  css: `.bgphoto{object-position:80% 50%}.kicker{margin-top:26px;font-size:16px}.fig{font-size:120px;margin-top:22px}.line{font-size:24px;margin-top:12px;max-width:560px}.src{font-size:13px;max-width:520px}.url{font-size:20px}`,
  body: `<div class="kicker">Cas d’usage · l’e-mail</div><div class="rule"></div>
<div class="fig">62,8 %</div>
<p class="line">d’ouverture moyenne sur <b>2 068 e-mails</b> envoyés aux fans identifiés.</p>
<div class="foot"><p class="src">Source : Bilan de saison Blue Penguin × HCC 2025-2026, slides 2 et 9 (4 campagnes Brevo)</p><p class="url">bluepenguin.ch</p></div>`,
};
