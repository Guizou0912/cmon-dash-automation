# BLUE PENGUIN — WORKFLOW SOCIAL MEDIA (INSTAGRAM + LINKEDIN)

**Version 1.1 — 13 novembre 2026** · sur le modèle GriddyPicks (V2 Routines + studio)
Demande : Douglas Finazzi, #blue-penguin, 12.11.2026.

> Principe : Claude prépare → l'équipe valide dans Slack → Claude crée un **brouillon Metricool** (marque Blue Penguin) → l'humain publie.
> **Aucune publication directe** sur Instagram, LinkedIn ou Meta.

---

## 1. Les deux canaux de validation

| Quoi | Canal | ID |
|---|---|---|
| Posts complets : texte + visuel joint (PNG, MP4 ; variantes GIF/miniature dans le fil) | #blue-penguin | `C09CAC4DNJC` |

Depuis le 16.11.2026, plus rien de Blue Penguin ne va dans #tsiory-daily (`C0BNJUMF4H2`) : chaque post part en un seul message dans #blue-penguin.

Validation : réaction ✅ = validé, ✏️ + réponse en fil = correction demandée. Claude corrige dans le fil, jamais en nouveau message.

## 2. Schéma

```text
Lundi : plan de la semaine
      │
      ▼
Claude : choisit les sujets (§4), vérifie les chiffres (§6), rédige (§7)
      │
      └──► Post complet (texte + visuel, skill blue-penguin-studio) ──► #blue-penguin C09CAC4DNJC  [BP:...]
                                     │
                                     ▼
                     Validation humaine (✅ / ✏️)
                                     │
                                     ▼
        Brouillon Metricool « Blue Penguin » (7424422) → publication humaine
```

## 3. Deux réseaux, deux publics

| | **LinkedIn** (B2B) | **Instagram** (B2C) |
|---|---|---|
| Cible | clubs, ligues, partenaires, marques (horlogerie, luxe) | fans des clubs équipés (HCC aujourd'hui) |
| Ton | **vouvoiement**, concret, expert ; « proposé et opéré par C'mon Sports » | **tutoiement**, phrases courtes, énergie (« ta fidélité », « tes points ») |
| Objectif | prouver le ROI, générer des rendez-vous / leads | inscriptions, connexions, scans, montée de niveau |
| Visuel | navy + photo, chiffre clé, source en pied | blanc + aplat cyan, ou navy match day |
| Format | 1080×1350 (doc/feed) ou 1200×627 | 1080×1350 feed, 1080×1920 story |

## 4. Calendrier type (à valider)

**3 publications par semaine**, chacune déclinée pour son réseau :

| Jour | Réseau | Famille | Visuel |
|---|---|---|---|
| Mardi | LinkedIn (+ Reel IG adapté si pertinent) | **Cas d'usage chiffré** (série UC01 → UC12) | **Motion** MP4 + GIF + son |
| Jeudi | Instagram | **Tuto fan** ou **Récompense** | **Motion** (Reel) |
| Jour de match HCC à domicile | Instagram (story + feed) | **Match day** : « Scanne ton billet » | **Motion** (Reel + story animée) |

Si pas de match à domicile dans la semaine : remplacer par **Produit** (M1 authentification / M3 collectibles & enchères) côté LinkedIn, ou **Communauté** (sondage, niveaux) côté Instagram.

### Familles de contenus

| Code | Famille | Réseau | Structure |
|---|---|---|---|
| CASUSAGE | Cas d'usage chiffré | LinkedIn | CHIFFRE → CE QUE ÇA VEUT DIRE POUR UN CLUB → SOURCE → CTA « Découvrir la solution » |
| PRODUIT | Authentification (M1), Collectibles & enchères (M3), Récompenses (M2) | LinkedIn | PROBLÈME → SOLUTION → PREUVE → CTA |
| COULISSES | Expertise suisse, C'mon Sports, certification ORIGYN | LinkedIn | HISTOIRE → PREUVE → CTA |
| TUTO | Comment gagner des points, les niveaux, l'app | Instagram | LEÇON → EXEMPLE → À TOI → CTA « Rejoins le programme » |
| RECOMPENSE | Lots, Soirée Blue Penguin, Top 20 (sans noms) | Instagram | RÉCOMPENSE → COMMENT L'OBTENIR → CTA |
| MATCHDAY | Rappel scan de billet, jour de match à domicile | Instagram | MATCH → GESTE → POINTS → CTA |
| COMMUNAUTE | Sondage, quiz, niveau du mois | Instagram | QUESTION → INTERACTION |

Ordre de la série cas d'usage (README kit HCC) : 01 → 02 → 03 → 04 à 10 → 11 → 12.

## 5. Marqueurs anti-doublon (Slack = journal)

```text
[BP:CASUSAGE:UC06:LINKEDIN]
[BP:TUTO:TUTO-002:INSTAGRAM]
[BP:MATCHDAY:2026-11-21:HCC-<ADVERSAIRE>:INSTAGRAM]
[BP:PRODUIT:M3:LINKEDIN]
```

Visuel : même marqueur suffixé `:VISUAL`. Avant d'écrire, rechercher le marqueur dans `C09CAC4DNJC` : trouvé → ne rien refaire.

## 6. Sources et règles de données

Sources autorisées, par ordre de confiance :

1. **Bilan de saison Blue Penguin × HCC 2025-2026** (slides citées) → tableau de vérification dans `docs/README_cas-usage-HCC.md`.
2. Convention de partenariat Blue Penguin × HCC (art. 4, enchères).
3. Données Brevo / dashboard du club **datées** (ex. état des automations du 12.11.2026 : 830 membres) — seulement avec la date de relevé.
4. Études externes **citées en toutes lettres** (ex. HBR, A. Gallo, 29.10.2014 : « 5 à 25× »).
5. bluepenguin.ch pour les fonctionnalités.

Règles :
- jamais de chiffre inventé, arrondi ou tronqué (« 5 à 25× », pas « 5× ») ;
- toujours la source en pied de visuel B2B et dans le message Slack ;
- **ne jamais publier de chiffre interne négatif** (bugs, doublons, taux de connexion) : ces données servent au pilotage, pas à la promo ;
- aucun nom de fan sans accord écrit ;
- photos générées = mises en scène, jamais présentées comme du HCC ;
- vocabulaire proscrit : crypto, token, investissement, spéculation.

## 7. Format Slack — TEXTE (#blue-penguin C09CAC4DNJC)

```text
[BP:CASUSAGE:UC06:LINKEDIN]
🐧 BLUE PENGUIN — POST À VALIDER

Réseau : LinkedIn            Publication conseillée : mardi 18.11, 8h30
Famille : Cas d'usage chiffré — le parcours fan
Chiffre : 99,6 % (775 / 778 parcours jusqu'au scan)
Source : Bilan de saison Blue Penguin × HCC 2025-2026, slide 10

TEXTE
<caption prête à copier>

CTA : Découvrir la solution → bluepenguin.ch
Hashtags : 3 max
Visuel : joint (variantes dans le fil)

Validation : ✅ ou ✏️ en fil
```

Règles de caption :
- **LinkedIn** : 600-1 200 caractères, accroche sur 2 lignes (avant « voir plus »), vouvoiement, 1 chiffre, 1 source, 1 CTA, 3 hashtags max, pas plus de 3 emojis.
- **Instagram** : 150-400 caractères, tutoiement, 1 CTA, lien en bio, 3-5 hashtags, 3 emojis max.
- Conventions suisses : « », CHF, ’.

## 8. Visuels joints au post (#blue-penguin C09CAC4DNJC)

Le message du post (§7) est l'`initial_comment` du visuel principal (`_son.mp4` ; un PNG seulement en secours). Les variantes d'un motion (`.mp4` muet, `_720.gif`, `_miniature.jpg`) et une Story éventuelle sont envoyées dans le fil de ce message.

## 9. Production des visuels

Skill **`blue-penguin-studio`** (`~/.claude/skills/blue-penguin-studio/SKILL.md`) et dossier `C:\Users\randr\Claude\BluePenguin\` — totalement séparés de GriddyPicks (charte, polices, gabarits, sons, sorties).

- **Motion → HyperFrames** : gabarit `hyperframes/bp-chiffre`, puis `hyperframes/bp_finalise.js`. Sert au cas d'usage chiffré de la semaine et aux stories match day. Livrables : `_son.mp4`, `.mp4` muet, `_720.gif`, `_miniature.jpg`.
- **Son → bibliothèque CC0 Barty-Bart** (`sound-kit/sfx`, 103 sons, avec manifest et licences). Les sons sont posés en `<audio>` dans la composition, et le niveau est mesuré sur le MP4 exporté.
- **Motion studio → `studio/bp_studio.js`** (`format: 'motion'`) : tout le reste. Depuis le 23.11.2026 (test à partir de W49), plus aucun post statique ; le format `png` ne sert qu'en secours si le rendu motion échoue 2 fois.

## 9 bis. Metricool

- **Marque** : Blue Penguin, blogId `7424422`, fuseau Europe/Zurich. Instagram `blue.penguin.official`, LinkedIn `urn:li:organization:110086834`, Facebook `266161149908983`.
- **Seulement après le ✅ dans Slack** : `createScheduledPost` avec `draft: true` (brouillon), à la date du créneau conseillé (`getBestTimeToPostByNetwork`). Le lien du brouillon (`plannerUrl`) est posté en réponse dans le fil Slack du post.
- **Médias** : URL publique, Dropbox ou Google Drive. Metricool n'accepte pas de fichier local. Le dossier Dropbox Blue Penguin reste à définir.
- **Instagram Reel** : `type: "REEL"`, vidéo `_son.mp4`, `videoThumbnailUrl` = la miniature, et `isAiGenerated: true` si la photo est générée.
- **LinkedIn** : le `.mp4` muet (le PNG seulement s'il a servi de secours).
- Jamais d'`autoPublish` sans accord explicite.

## 10. Décisions (13.11.2026)

1. **Police** : celle de la charte v1.0, Outfit 500 pour les titres et Inter pour le texte et les chiffres. Les kits antérieurs à la charte ne servent plus de modèle typographique.
2. **Logo** : en bas à droite (charte §6), en navy ou en blanc sur un aplat cyan.
3. **Barèmes de points** : pas affichés tant qu'ils ne sont pas sourcés. Le tuto présente donc des étapes 1-2-3.
4. **Compte** : un compte Blue Penguin propre, relié via Metricool (blogId 7424422).
5. **Motion** : HyperFrames. **Son** : bruitages CC0 Barty-Bart.

## 11. Encore ouvert

- Cadence de 3 posts par semaine, à confirmer avec Douglas.
- Dossier Dropbox (ou Drive) où déposer les visuels validés pour Metricool.
- Routine cloud « lundi » comme pour GriddyPicks. Elle nécessite un dépôt GitHub contenant les gabarits et le kit son.
