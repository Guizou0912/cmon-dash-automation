---
name: blue-penguin-studio
description: Studio visuels, motion design (HyperFrames) et son (bruitages CC0 Barty-Bart) de Blue Penguin, le programme de fidélité des fans opéré par C'mon Sports, avec programmation Metricool. À utiliser pour tout visuel, animation, Reel, GIF, vidéo avec bruitages ou post Instagram / LinkedIn Blue Penguin (cas d'usage chiffrés, tutos fans, récompenses, match day). Ne jamais l'utiliser pour GriddyPicks, et ne jamais réutiliser les gabarits, couleurs ou sons GriddyPicks pour Blue Penguin.
---

# Blue Penguin Studio : visuels, motion HyperFrames, son, Metricool

Tout se trouve dans `C:\Users\randr\Claude\BluePenguin\`, à l'écart de GriddyPicks :

| Dossier | Rôle |
|---|---|
| `hyperframes/bp-chiffre/` | **gabarit motion HyperFrames** « Chiffre clé » (feed 1080×1350, 7 s, avec son) |
| `hyperframes/bp_finalise.js` | finalisation : son normalisé, version muette, GIF 720, miniature, mesure LUFS |
| `studio/bp_studio.js` + `studio/exemples/` | **motion studio** (`format: 'motion'`, mises en page `tuto.js` / `linkedin.js`, animation et sons de `chiffre.js`) ; PNG seulement en secours |
| `assets/` | logos (`logo_cyan` / `logo_blanc` / `logo_navy`), symbole, fan card, `elements/` (médailles, icônes), `photos/` (sans texte) |
| `sound-kit/sfx/` | **bibliothèque CC0 Barty-Bart** : 103 sons, `manifest.json`, `LICENSES_sons_CC0.md`, `TOP-PICKS.md` |
| `docs/BLUE_PENGUIN_WORKFLOW.md` | calendrier, Slack, sources, Metricool |
| `production/semaine-XX/` | sorties de la semaine |

Ne jamais écrire de fichier Blue Penguin dans `Claude\GriddyPicks\`, et inversement.

## Quel outil pour quel contenu

| Contenu | Outil | Livrables |
|---|---|---|
| Cas d'usage chiffré de la semaine (Reel + vidéo LinkedIn), stories match day | **HyperFrames** | `_son.mp4`, `.mp4` muet, `_720.gif`, `_miniature.jpg` |
| Tuto, récompense, communauté, match day, produit LinkedIn (depuis le 23.11.2026 : plus aucun post statique) | `bp_studio.js` (format `motion`, 6-7 s, message lisible avant 1 s) | `_son.mp4`, `.mp4` muet, `_720.gif`, `_miniature.jpg` (PNG en secours seulement, signalé « ⚠️ SECOURS PNG ») |

## Motion avec HyperFrames : la boucle de travail

Pré-requis : FFmpeg et ffprobe, installés via winget (Gyan.FFmpeg). Dans Git Bash, ajouter le dossier à la session :
`export PATH="$LOCALAPPDATA/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin:$PATH"`

Si les skills HyperFrames (`/hyperframes`, `/hyperframes-cli`, `/media-use`) sont installés, les charger d'abord. Leur installation reste une étape de l'utilisateur : `npx hyperframes skills update`.

1. **Copier le gabarit** : `hyperframes/bp-chiffre/` vers `production/semaine-XX/<sujet>/`, en gardant `assets/fonts` et `assets/sfx`.
2. **Changer les données dans `index.html`** :
   - le texte de `#kicker`, `#line` et `#src` ;
   - `DATA.value` et `DATA.decimals` ;
   - la photo `assets/photo.jpg`.

   Chaque chiffre est sourcé (workflow §6).
3. **Contrôler** : lancer `npm run check`. Il ne doit rester aucune erreur. On peut garder ces avertissements :
   - `nested_structure` ;
   - `text_below_floor` sur la source (22 px, mention légale) ;
   - `clip_media_fit` s'il est voulu.
4. **Regarder les images** : lancer `npx hyperframes snapshot --at 0.5,1.5,6.5`, puis lire la `contact-sheet.jpg` avant tout rendu.
5. **Rendre** : `npx hyperframes@0.9.41 render -o renders/_rendu-brut.mp4`.
6. **Finaliser** : `node ..\..\..\hyperframes\bp_finalise.js renders/_rendu-brut.mp4 renders/BP_<TYPE>_<AAAA-MM-JJ>_<SUJET>`. Le script affiche les LUFS et la crête mesurés sur le fichier exporté, en stéréo et en mono.

Règles HyperFrames à respecter :
- une timeline GSAP en pause enregistrée dans `window.__timelines["main"]` ;
- un `data-start` et un `data-duration` sur chaque élément temporisé, et `class="clip"` sur chaque élément visuel ;
- aucun `Math.random()`, `Date.now()` ni appel réseau ;
- polices chargées en local (`assets/fonts`, Outfit 500 et Inter 400/600) ;
- format feed : `data-width="1080" data-height="1350"`. Pour une story : 1080×1920 (zone utile centrée de 1080×1420). Pour LinkedIn : 1920×1080 ou 1080×1080.

### Langage de mouvement

- **Calme et premium** : `power3.out` / `power4.out`, déplacements de 20 à 40 px, zoom lent de la photo (de 1,08 à 1 sur toute la durée). Pas de rotation, de shake, de flash, de blur agressif ni de whip.
- **Rythme du chiffre clé** :
  - 0,1 s : kicker ;
  - 0,3 s : trait cyan ;
  - 0,7 s : le chiffre apparaît ;
  - 0,8 à 2,2 s : il compte jusqu'à sa valeur ;
  - 2,4 s : la phrase ;
  - 3,1 s : le pied (source et logo) ;
  - ensuite, l'image reste tenue pendant au moins 3 s.
- `back.out` est réservé au logo et aux pastilles de points.
- Une idée par animation : jamais deux compteurs en même temps. Durée de 6 à 8 s pour un feed, de 10 à 15 s pour une story.

## Son : bibliothèque Barty-Bart (CC0)

Source : dépôt `Barty-Bart/motion-graphics`, skill `sound-effects`. Méthode de « sound pass » de Vox (@Voxyz_ai), crédit à conserver. Le mode d'emploi complet est dans `sound-kit/BARTY-BART_sound-effects_SKILL.md`.

Règles reprises :
- un vrai son par cue, jamais de bip synthétisé en code ;
- on choisit d'abord le **default_kit** du `manifest.json` ;
- on mesure le **MP4 exporté**, jamais le fichier intermédiaire ;
- on ne dit jamais « ça sonne bien » : on donne au client les chiffres et 3 à 5 timestamps à écouter au casque.

Identité Blue Penguin : **une « validation » chaleureuse**, pas le son gaming ou impact de GriddyPicks.

| Moment à l'écran | Catégorie | Fichier conseillé (`sfx/`) | Volume |
|---|---|---|---|
| Entrée de la photo ou d'un bloc | whoosh | `kit/whoosh.ogg` (2 images en avance) | 0,45 |
| Kicker ou trait | click | `kit/click.ogg` | 0,5 |
| Montée avant le chiffre | riser | `kit/riser.ogg`, **se termine** à l'arrivée du chiffre | 0,35 |
| Compteur en cours | tick | `kit/tick.ogg` et `tick/fs528561.ogg` en alternance, de plus en plus espacés | 0,28 à 0,35 |
| Chiffre atteint, certification, scan validé | ding | `ding/fs-571513-soft-notifications-bell-ding-d.ogg` (ou `kenney-interface-confirmation-00x`) | 0,6 |
| Logo ou pastille de points | pop | `pop/fs527522.ogg` | 0,6 |
| Changement de scène (story) | transition | `transition/fs-786514-swoosh-v2.ogg` | 0,4 |

- **Interdits** : `impact/*` lourds (cinematic, michael-bay, dramatic), `glitch/*` (imagerie tech et crypto), musique intégrée. Sur Instagram, la musique s'ajoute dans l'app.
- **Dans HyperFrames**, chaque son est un `<audio src="assets/sfx/x.ogg" data-start data-duration data-volume>`. La `data-duration` doit être égale à la durée du fichier (sinon `check` le signale).
- **Mixage** : `bp_finalise.js` vise −16 LUFS avec une crête vraie sous −4,5 dBFS. Un clip qui n'a que des bruitages plafonne vers −19 LUFS, parce que la limite de crête passe en premier : c'est normal. Il faut le dire au client et ne pas pousser plus fort.
- **Licences** : ne jamais ajouter de son Mixkit ou Pixabay dans `sound-kit/` (redistribution interdite). On ne garde que du CC0, avec une ligne dans `LICENSES_sons_CC0.md`.

## Charte (version 1.0, octobre 2026) : arbitrages pris le 13.11.2026

- **Polices** : celles de la charte. Titres en **Outfit 500** (interlettrage −1px), texte en **Inter 400**, chiffres clés en **Inter 600**. Les kits plus anciens (police large grasse et kicker doré) ne servent plus de modèle typographique. Il n'y a pas d'or dans la palette.
- **Logo en bas à droite** sur tous les visuels, comme le demande la charte §6 :
  - cyan sur fond blanc ou navy ;
  - **navy ou blanc sur un aplat cyan**, jamais cyan sur cyan ;
  - le logo du club se place à sa gauche, jamais à sa place.
- **Couleurs autorisées seulement** : `#40E4FC`, `#04CEEC`, `#0E9FBF` (24 px et plus), `#14213D`, `#0B1B33`, `#5B6578`, blanc, `#EEF1F6`. Au plus 3 couleurs par visuel, dans les proportions 60 % fond, 30 % cyan, 10 % encre.
- **Contraste** : pas de texte blanc sur cyan, et le cyan n'est jamais une couleur de texte sur fond blanc.
- **Texte à l'image** : un titre de 6 mots maximum et une ligne en Inter. Un seul appel à l'action par visuel. Le disque cyan porte le chiffre clé.
- **Chiffres** : aucun barème de points, aucun prix ni aucun pourcentage sans source écrite. Les +250 / +100 / +20 d'une maquette ne sont **pas** sourcés et ne s'affichent pas tant qu'ils ne sont pas confirmés.
- **Conventions suisses** : « », CHF, apostrophe ’, espace fine avant %.
- **Interdit** : imagerie crypto, dégradés violets, plus de 3 emojis, les mots crypto, token, investissement et spéculation.
- **Personnes** : aucun nom de fan. Les photos générées sont des mises en scène, jamais présentées comme des photos du club.

## Livraison : Slack, puis Metricool

1. **Post complet** dans #blue-penguin (`C09CAC4DNJC`) : un seul message par post avec le marqueur `[BP:...]`, le texte et le visuel principal joint (variantes d'un motion dans le fil). Plus rien ne va dans #tsiory-daily (`C0BNJUMF4H2`) depuis le 16.11.2026.
2. Validation ✅ ou ✏️ en fil sur ce message.
3. **Après validation (✅)**, programmer sur **Metricool, marque « Blue Penguin » (blogId `7424422`, fuseau Europe/Zurich)** :
   - réseaux connectés : Instagram `blue.penguin.official`, LinkedIn (`urn:li:organization:110086834`) et Facebook ;
   - outil `createScheduledPost` avec **`draft: true`** : on crée un brouillon, l'humain publie. Jamais `autoPublish` sans accord explicite ;
   - `media` doit être une **URL publique, Dropbox ou Google Drive**, pas un fichier local ;
   - un Reel se programme avec `instagramData.type: "REEL"` et la vidéo `_son.mp4`, plus `videoThumbnailUrl` (la miniature) ;
   - sur LinkedIn, on envoie le `.mp4` muet (le PNG seulement s'il a servi de secours) ;
   - `isAiGenerated: true` sur Instagram dès qu'une photo générée est utilisée.

## Avant d'envoyer : liste de contrôle

- [ ] Chaque chiffre est sourcé, et la source apparaît en pied de visuel (B2B) et dans le message Slack.
- [ ] Le titre fait 6 mots maximum, il n'y a qu'un appel à l'action, et le logo est en bas à droite dans la bonne couleur.
- [ ] Le `check` HyperFrames ne renvoie aucune erreur, et la contact-sheet a été lue.
- [ ] `bp_finalise.js` a été lancé, et ses LUFS et sa crête sont reportés dans le message Slack avec 3 timestamps à écouter.
- [ ] Le brouillon Metricool n'est créé qu'**après** le ✅ Slack.
