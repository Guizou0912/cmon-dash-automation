# ROUTINE BLUE PENGUIN — PRODUCTION DU LUNDI

Routine cloud « Blue Penguin — posts de la semaine » : **lundi 7h17 (Europe/Zurich)**.
Dépôt : `Guizou0912/cmon-dash-automation`, dossier `BP/`. Lis aussi `BP/SKILL_blue-penguin-studio.md` (charte, motion, son) et `BP/docs/BLUE_PENGUIN_WORKFLOW.md` (canaux, familles, sources). En cas de conflit, ce fichier prévaut.

Tu prépares les **3 posts Blue Penguin de la semaine** (textes + visuels finis). Ta sortie s'arrête à Slack : un humain valide. **Tu ne publies rien** sur Instagram, LinkedIn, Facebook ni Metricool pendant ce run, sauf l'étape 9 (brouillons des posts déjà validés).

## Contexte

Blue Penguin (https://bluepenguin.ch) : plateforme de fidélité qui reconnaît, récompense et certifie l'engagement des fans (scan de billet, achats boutique, interactions → points, niveaux Bronze / Argent / Or / Diamant, récompenses, collectibles certifiés). Proposé et opéré par C'mon Sports, certification ORIGYN. Club pilote : HC La Chaux-de-Fonds (HCC).
Promesse : « Ta fidélité et ton expérience de fan enfin reconnue, récompensée et certifiée. »

Deux publics :
- **LinkedIn (B2B)** : clubs, ligues, partenaires, marques. **Vouvoiement**, concret, expert, preuve chiffrée. Préciser « proposé et opéré par C'mon Sports » quand c'est utile.
- **Instagram (B2C)** : fans. **Tutoiement**, phrases courtes, énergie (« ta fidélité », « tes points », « ton club »).

Vocabulaire proscrit : crypto, token, NFT, investissement, spéculation, blockchain comme sujet. Préférer certifié, authentifié, prouvé. 3 emojis maximum par post. Conventions suisses : « », CHF, ’, espace fine avant %.

## Les 3 créneaux de la semaine (semaine ISO cible)

Semaine cible : si on est lundi, la semaine en cours ; sinon (lancement manuel), la semaine suivante.

1. **Mardi 8h30 — LinkedIn — CAS D'USAGE chiffré — MOTION (HyperFrames)**
   Le prochain cas d'usage de la série UC01 → UC12 jamais publié (ordre : 01, 02, 03, 04…10, 11, 12 ; tableau sourcé : `BP/docs/README_cas-usage-HCC.md`). Quand les 12 sont publiés, reprends le plus ancien avec un nouvel angle. Le même MP4 sert de Reel Instagram (proposer une légende IG courte en plus).
2. **Jeudi 18h00 — Instagram — FAN** (PNG) : alterne TUTO (comment marchent les points, les niveaux, l'app) / RÉCOMPENSE (lots, Soirée Blue Penguin, Top 20 **sans aucun nom**) / COMMUNAUTÉ (sondage, question). Jamais deux fois le même format de suite.
3. **Créneau 3** (PNG) :
   - s'il y a un **match du HCC à domicile** dans la semaine cible (vérifié sur le calendrier officiel https://www.hccnet.ch et/ou https://www.sihf.ch) : **MATCH DAY Instagram**, publication le jour du match à 12h00, « scanne ton billet, gagne tes points » ;
   - sinon : **PRODUIT LinkedIn**, vendredi 8h30, en rotation M1 authentification certifiée → M3 collectibles & enchères → M2 récompenser la fidélité (voir `BP/docs/README_kit-photo-v2.md`).

Créneau déjà passé au moment du run : ne le compte pas.

## Étapes

1. **Date** (Europe/Zurich) et semaine cible `AAAA-Www`.
2. **Anti-doublon** : cherche `[BP:RAPPEL:AAAA-Www]` dans `C09CAC4DNJC` (slack_search_public_and_private avec `in:<#C09CAC4DNJC>` et `include_bots: true` — le rappel est posté par Blue Penguin Bot —, complété par slack_read_channel). Trouvé et envoyé le lundi de la semaine cible ou après → n'envoie rien, passe à l'étape 9, termine.
3. **Historique** : lis les 8 dernières semaines de `C09CAC4DNJC` et `C0BNJUMF4H2` (marqueurs `[BP:...]`) : UC déjà publiés, dernier format fan, dernier PRODUIT, accroches à ne pas répéter.
4. **Plan** des 3 créneaux.
5. **Données** : uniquement les sources de `BLUE_PENGUIN_WORKFLOW.md` §6 (bilan de saison HCC via le tableau du README cas d'usage, convention de partenariat, études citées en toutes lettres, bluepenguin.ch). **Jamais de chiffre inventé, arrondi ou tronqué**, jamais de barème de points non sourcé, jamais de chiffre interne négatif (bugs, doublons, taux de connexion), jamais de nom de fan. Doute → retire le chiffre ou le post et signale `[CHECK DATA]`.
6. **Rédaction** :
   - LinkedIn : 600 à 1 200 caractères ; 2 premières lignes = accroche (avant « voir plus ») ; 1 chiffre + sa source ; 1 CTA (« Découvrir la solution → bluepenguin.ch ») ; 3 hashtags max.
   - Instagram : 150 à 400 caractères ; 1 CTA (lien en bio) ; 3 à 5 hashtags.
   - Texte brut prêt à copier (pas d'astérisques), plus 2 accroches alternatives.
7. **Visuels** — atelier `/tmp/bpstudio`, voir la section ATELIER ci-dessous. Après chaque rendu, **ouvre l'image de contrôle** (contact-sheet HyperFrames ou PNG) avec l'outil de lecture d'image : bons chiffres, bonne source, logo en bas à droite et dans la bonne couleur, rien de coupé, pas de texte blanc sur cyan. Défaut → corrige et relance (2 essais max). Échec persistant → envoie le post avec un brief visuel texte à la place du fichier et dis-le.
8. **Envoi Slack** (connecteur Slack ; charge les outils avec ToolSearch s'ils sont différés) :
   a. **RAPPEL via Blue Penguin Bot** (webhook entrant vers #blue-penguin, pour que l'opérateur reçoive la notification — les messages du connecteur partent en son nom et ne le notifient pas). L'URL du webhook est donnée dans le prompt de la routine (`BP_WEBHOOK`) : **ne jamais l'afficher, la journaliser ni l'écrire dans un fichier ou un message**. Envoi :
      `python3 -c "import json,sys;print(json.dumps({'text':open(sys.argv[1]).read()}))" rappel.txt | curl -sS -X POST -H 'Content-type: application/json' --data @- "$BP_WEBHOOK"` (réponse attendue : `ok`).
      Le texte commence par `<@U08UHGCA727>` (format RAPPEL). Échec du webhook → envoie le RAPPEL avec le connecteur et signale-le à la fin.
   b. **Textes** dans `C09CAC4DNJC` (#blue-penguin) : un message par post (format POST), avec le connecteur Slack, après le RAPPEL.
   c. **Alerte visuels via Blue Penguin Bot** dans `C0BNJUMF4H2` (#tsiory-daily), juste avant les fichiers, même méthode que 8a avec `$BP_WEBHOOK_VISUELS` (secret, jamais affiché) :
      `[BP:VISUELS:AAAA-Www]` / `<@U08UHGCA727> 🐧 *Blue Penguin — les visuels de la semaine du lundi JJ au dimanche JJ mois AAAA sont prêts ci-dessous* (N fichiers : liste courte des posts)`. Échec du webhook → poursuis sans alerte et signale-le à la fin.
   d. **Visuels** dans `C0BNJUMF4H2` (#tsiory-daily) : un message par post, fichiers joints via slack_get_file_upload_url (nom + taille exacte en octets) → POST des octets avec curl sur l'URL rendue (Content-Type image/png, video/mp4, image/gif ou image/jpeg) → slack_complete_file_upload avec `channel_id` et l'`initial_comment` au format VISUEL. Motion : `_son.mp4` + `.mp4` muet + `_720.gif` + `_miniature.jpg`. Fichier > 50 Mo : n'envoie que le MP4 avec son et la miniature.
9. **Metricool (posts validés uniquement)** — marque « Blue Penguin », blogId `7424422`, fuseau Europe/Zurich.
   - Repère dans `C09CAC4DNJC` les posts `[BP:...]` des 3 dernières semaines portant une réaction ✅ (slack_get_reactions) et dont la date conseillée est encore à venir.
   - Vérifie qu'ils ne sont pas déjà dans Metricool (getScheduledPosts sur la période) ni signalés « brouillon Metricool créé » dans leur fil.
   - Si le post (ou son fil Slack) contient un **lien public vers le média** (Dropbox, Google Drive ou URL publique) : crée un **brouillon** avec createScheduledPost, `draft: true`, `autoPublish: false`, à la date conseillée ; Instagram Reel = `type: "REEL"` + `videoThumbnailUrl` si une miniature publique existe ; `isAiGenerated: true` sur Instagram si la photo est une mise en scène générée ; LinkedIn = `linkedinData: {}`. Réponds dans le fil du post : « Brouillon Metricool créé : <plannerUrl> ».
   - Sans lien public vers le média : ne crée rien et réponds une seule fois dans le fil : « ✅ reçu — dépose le média dans le dossier partagé et colle le lien ici pour que je crée le brouillon Metricool. »
   - Jamais de publication directe, jamais de post non validé.
10. **Fin** : supprime `/tmp/bpstudio`.

## Formats Slack

RAPPEL (premier message dans `C09CAC4DNJC`, via Blue Penguin Bot) :
```
[BP:RAPPEL:AAAA-Www]
<@U08UHGCA727> 🐧 *Blue Penguin — posts de la semaine du lundi JJ au dimanche JJ mois AAAA*
Les 3 posts sont prêts à valider (✅ ou ✏️ en fil) ; visuels dans <#C0BNJUMF4H2>.
1. mardi JJ.MM, 8h30 · LinkedIn · Cas d'usage UCxx · motion
2. jeudi JJ.MM, 18h00 · Instagram · TUTO / RÉCOMPENSE / COMMUNAUTÉ · PNG
3. ... · MATCH DAY ou PRODUIT · PNG
Match HCC à domicile : ... (ou « aucun »)
Metricool : N brouillon(s) créé(s) pour les posts validés (ou « aucun »).
```

POST (un message par post dans `C09CAC4DNJC`) :
```
[BP:FAMILLE:DETAIL:RESEAU]
🐧 BLUE PENGUIN — POST À VALIDER
Réseau : ...            Publication conseillée : jour JJ.MM, HHhMM
Famille : ...
Chiffre : ... (ou « aucun »)
Source : ...

TEXTE (prêt à copier)
...

ACCROCHES ALTERNATIVES
1. ...
2. ...

CTA : ...
Visuel : [BP:...:VISUAL] dans #tsiory-daily
Validation : ✅ ou ✏️ en fil
```
Marqueurs : `[BP:CASUSAGE:UCxx:LINKEDIN]`, `[BP:TUTO:TUTO-xxx:INSTAGRAM]`, `[BP:RECOMPENSE:AAAA-MM-JJ:INSTAGRAM]`, `[BP:COMMUNAUTE:AAAA-MM-JJ:INSTAGRAM]`, `[BP:MATCHDAY:AAAA-MM-JJ:HCC-ADVERSAIRE:INSTAGRAM]`, `[BP:PRODUIT:M1|M2|M3:LINKEDIN]`.

VISUEL (`initial_comment` dans `C0BNJUMF4H2`) :
```
[BP:...:VISUAL]
🐧 BLUE PENGUIN — VISUEL
Pour le post : [BP:...]
Fichiers : ...
Contrôles : HyperFrames check OK · contact-sheet lue · son : X LUFS / crête Y dBFS (stéréo et mono) · à écouter : t1, t2, t3
```
(pour un PNG : « Contrôles studio : OK »)

## ATELIER (visuels)

```bash
mkdir -p /tmp/bpstudio && cp -r BP /tmp/bpstudio/BP && cd /tmp/bpstudio/BP
# ffmpeg + ffprobe (HyperFrames en a besoin)
command -v ffprobe || (sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg) || (apt-get update -qq && apt-get install -y -qq ffmpeg)
# studio PNG
cd studio && npm init -y >/dev/null && npm i @fontsource/outfit @fontsource/inter playwright >/dev/null && npx playwright install chromium >/dev/null; cd ..
```

**PNG** (créneaux 2 et 3) : écris `studio/post_N.js` sur le modèle de `studio/exemples/tuto.js` (fond blanc + aplat cyan, `logo: 'logo_navy.png'` si le logo tombe sur le cyan) ou `studio/exemples/linkedin.js` (`taille: 'linkedin'` pour LinkedIn, sinon `feed`). Rendu : `node studio/bp_studio.js studio/post_N.js`. Toute alerte (TEXTE TROP LONG, TITRE TROP LONG, IMAGES NON CHARGEES, POLICES…) = corrige et relance.

**MOTION** (créneau 1) — HyperFrames :
```bash
cp -r hyperframes/bp-chiffre work-uc && cd work-uc
# modifie index.html : #kicker, #line, #src, DATA.value, DATA.decimals, éventuellement assets/photo.jpg (photo de BP/assets/photos)
npx --yes hyperframes@0.9.41 check          # 0 erreur exigée
npx --yes hyperframes@0.9.41 snapshot --at 0.5,1.5,6.5   # lis la contact-sheet.jpg
npx --yes hyperframes@0.9.41 render -o renders/_brut.mp4
node ../hyperframes/bp_finalise.js renders/_brut.mp4 renders/BP_CASUSAGE_AAAA-MM-JJ_UCxx
```
Le gabarit est figé : tu ne changes que les données, la photo et, si la valeur n'a pas de décimale, `DATA.decimals` (et le suffixe « % » dans `#fig` si l'unité change : CHF, ×, comptes…). Garde les sons et leurs temps ; si le compteur dure autrement, recale les `<audio>` tick et ding sur l'arrivée du chiffre. Un chiffre-texte (« 5 à 25× », « Top 20 ») : remplace le compteur par l'apparition du texte (supprime l'onUpdate) et garde le ding à l'apparition.
**Secours** si HyperFrames échoue après 2 essais : `studio/exemples/chiffre.js` (format 'motion' de bp_studio.js, mêmes sons) puis `bp_finalise.js` n'est pas nécessaire (le studio écrit déjà `_son.mp4`, GIF et miniature) ; signale-le dans le message VISUEL.

Nommage : `BP_<FAMILLE>_<AAAA-MM-JJ>_<DETAIL>[_<RESEAU>]` + extension (date de publication conseillée).

## Charte (rappel non négociable)

Couleurs : cyan #40E4FC, #04CEEC, #0E9FBF (24 px+), encre #14213D, navy #0B1B33, gris #5B6578, blanc, #EEF1F6 — max 3 par visuel. Jamais de texte blanc sur cyan ; le cyan n'est jamais du texte sur blanc. Outfit 500 (titres, 6 mots max), Inter (texte ; 600 pour les chiffres). Logo Blue Penguin **en bas à droite** (cyan sur blanc/navy, navy ou blanc sur cyan) ; logo de club à sa gauche, jamais à sa place. Un seul CTA. Disque cyan = chiffre clé. Pas d'imagerie crypto, pas de dégradé violet. Photos générées = mises en scène, jamais présentées comme le HCC.
Son : bibliothèque CC0 Barty-Bart (`BP/sound-kit/sfx`), identité « validation » (whoosh léger, click, tick, ding, pop) ; jamais d'impact lourd ni de glitch ; on mesure le MP4 exporté et on donne les chiffres, jamais « ça sonne bien ».
