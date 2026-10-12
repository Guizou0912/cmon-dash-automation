# Routine hebdomadaire — Dash Performance C'mon Sports

Tu tournes chaque lundi matin dans une session cloud, sans intervention humaine. Le dépôt cloné contient les scripts. Ta mission : produire les livrables hebdomadaires des 8 clubs (CHAM, FOB, FOXES, HCC, LION, LS, SVWE, YS) et les publier dans le canal Slack `C0BNJUMF4H2`, puis y poster un verdict explicite.

## Règles absolues

- **Ne jamais afficher, logger ni poster une clé API.** Les clés sont dans les variables d'environnement `BREVO_KEY_<CLUB>` ; les scripts les lisent seuls. N'exécute jamais `env`, `printenv` ou `echo $BREVO_KEY_…`.
- **Ne jamais inventer une donnée.** Une valeur manquante reste vide et est signalée dans le verdict.
- **Ne jamais poster de CSV** ni de fichier contenant des données personnelles en dehors du zip des classeurs prévu à l'étape 8.
- Un club en échec n'arrête pas les autres. Un statut « terminé » sans verdict ne vaut rien : le verdict de l'étape 9 est obligatoire, même en cas d'échec partiel.

Dans la suite, `JJMMAA` = date du jour à Europe/Zurich (ex. `191026`) et `JJMM` = jour + mois (ex. `1910`). Calcule-les avec `TZ=Europe/Zurich date +%d%m%y`.

## Étapes

1. **Dépendances** : `pip install -r requirements.txt`.

2. **État de la semaine précédente.** Lis l'historique du canal `C0BNJUMF4H2` (connecteur Slack) sur les 10 derniers jours et repère le fichier le plus récent nommé `etat_dash_<JJMMAA>.json`. Récupère son contenu (lecture de fichier Slack) et écris-le **tel quel** dans `etat_prec.json` à la racine du dépôt. Puis : `python cmon_etat.py --restore etat_prec.json`.
   Si aucun fichier d'état n'est trouvé : continue quand même (les livrables sortiront sans évolutions ni historique) et signale-le en tête du verdict.

3. **Extraction Brevo** : `python cmon_brevo.py --extract` (environ 20 minutes, LS compte ~95 000 contacts). Lis ensuite `Fichier ZIP _/JJMMAA/_rapport_extraction.json` : statut, volumes et anomalies par club.
   Si une requête échoue en `403` avec `x-deny-reason: host_not_allowed`, c'est la liste blanche réseau de l'environnement : signale-le.

4. **Captures de délivrabilité.** Dans le canal, cherche les images postées depuis 3 jours nommées `<CLUB> <JJMM>.png` (ex. `HCC 1910.png`). Pour chacune, ouvre l'image, relève le **score au centre du cercle** et la **fenêtre de dates** en haut, puis écris `Fichier ZIP _/JJMMAA/delivrabilite.json` au format :
   `{"HCC": {"score": 78, "fenetre": "12.09 → 11.10.2026"}, …}`
   Un club sans capture est absent du fichier et listé dans le verdict. Ne recopie jamais le score de la semaine précédente.

5. **Classeurs Looker** : `python cmon_classeurs.py --etat etat_prec.json` (sans `--etat` si l'étape 2 n'a rien trouvé). Vérifie dans `_rapport_classeurs.json` que `problemes_formules` est vide pour chaque club.

6. **Page KPI** : `python cmon_kpi_html.py --etat etat_prec.json` → `Fichier ZIP _/JJMMAA/KPI_JJMMAA.html`.

7. **Nouvel état** : `python cmon_etat.py` → `Fichier ZIP _/JJMMAA/etat_dash_JJMMAA.json`.

8. **Publication Slack**, dans cet ordre, pour chacun des fichiers :
   - `Fichier ZIP _/JJMMAA/KPI_JJMMAA.html`
   - `CMON_Dash_JJMMAA.zip` : crée-le avec `cd "Fichier ZIP _/JJMMAA" && python -m zipfile -c ../../CMON_Dash_JJMMAA.zip "A UPLOADER" "NON UPLOADE - calculs et notes"`
   - `Fichier ZIP _/JJMMAA/etat_dash_JJMMAA.json`

   Pour chaque fichier : taille exacte en octets (`wc -c < fichier`) → `slack_get_file_upload_url` (filename, content_length) → mets l'URL dans une variable shell et envoie les octets avec `curl -X POST "$URL" -H "Content-Type: <type>" --data-binary @fichier` (text/html, application/zip, application/json) → `slack_complete_file_upload` avec `channel_id = C0BNJUMF4H2`. Commentaire du KPI : 3 à 5 puces avec les chiffres clés de la semaine. Commentaire du zip : « Classeurs Looker à uploader — relevé du JJ.MM.AAAA ». Commentaire de l'état : « État technique de la routine — ne pas supprimer ».

9. **Verdict** (message Slack dans le canal, obligatoire) :
   - en tête : ✅ si les 8 clubs sont extraits sans anomalie bloquante, ⚠️ sinon, ❌ si rien n'a pu être publié ;
   - tableau par club : base totale (évolution), exploitables, engagés, actif total, non-engagés, billetterie, score de délivrabilité ou « capture manquante » ;
   - anomalies : clubs en échec et pourquoi, segments introuvables, contrôles en échec (exploitables ≠ segment, engagés hors actif total, orphelins), état précédent absent, captures manquantes ;
   - durée totale et nombre d'appels API (dans `_rapport_extraction.json`).
   Volumes en format suisse : espace pour les milliers, virgule décimale, `71,69 % (+0,01)`.

## Contexte métier (pour lire les résultats, pas pour les modifier)

- Segments Brevo résolus par nom : engagés = `CMON-Actifs-6m-réels-(hors MPP)`, actif total = `CMON-Actifs-6m`, non-engagés = `CMON-Sunset-24m-plus`, billetterie = `Billetterie Active Saison 26-27`. Exploitables = contacts non blacklistés, contrôlés contre le segment `Contacts Exploitables`.
- LS n'a ni segment actif total, ni billetterie, ni `SOURCE_ACQUISITION` : c'est normal, pas une anomalie.
- Quelques contacts à la fois engagés et non-engagés : chevauchement connu des définitions Brevo, information seulement.
- Abonnements (billetterie) : pas encore automatisés, rien à faire.
