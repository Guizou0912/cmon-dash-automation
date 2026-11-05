# Routine hebdomadaire — exports Brevo des 9 comptes C'mon Sports

Tu tournes chaque lundi matin dans une session cloud, sans intervention humaine. Le dépôt cloné contient `cmon_brevo.py` (bibliothèque standard Python uniquement, rien à installer). Ta mission : extraire les exports Brevo des 9 comptes (8 clubs : CHAM, FOB, FOXES, HCC, LION, LS, SVWE, YS ; plus le compte santé SANTE), les mettre dans **un seul zip**, le poster dans le canal Slack `C0BNJUMF4H2`, puis poster un verdict.

## Règles absolues

- **Ne jamais afficher, logger ni poster une clé API.** Les clés sont dans les variables d'environnement `BREVO_KEY_<CLUB>` et le script les lit seul. N'exécute jamais `env`, `printenv` ni `echo` sur ces variables.
- **Ne jamais inventer une donnée.** Un club en échec est signalé, pas complété.
- Un club en échec n'arrête pas les autres. Le verdict de l'étape 4 est obligatoire, même si tout a échoué.

`JJMMAA` = date du jour à Europe/Zurich : `TZ=Europe/Zurich date +%d%m%y`.

## Étapes

1. **Extraction** : `python cmon_brevo.py --extract` (environ 20 minutes ; LS compte ~95 000 contacts). Le script écrit `Fichier ZIP _/JJMMAA/` : par club `Contacts totaux`, `Contacts exploitables `, `Contacts engagés`, `Contacts non-engagés`, `ACTIF TOTAL`, `Billetterie Active Saison 26-27`, `email-campaigns-<début>_<fin>` (3 mois), plus `_rapport_extraction.json`.
   Si une requête échoue en `403` avec `x-deny-reason: host_not_allowed`, c'est la liste blanche réseau de l'environnement : dis-le dans le verdict.

2. **Zip** : `cd "Fichier ZIP _" && python -m zipfile -c ../exports_brevo_JJMMAA.zip JJMMAA`

3. **Publication Slack** du fichier `exports_brevo_JJMMAA.zip` :
   - taille exacte : `wc -c < exports_brevo_JJMMAA.zip`
   - `slack_get_file_upload_url` avec `filename` et `content_length` exacts
   - mets l'URL dans une variable shell, sans la modifier, et envoie les octets : `curl -X POST "$URL" -H "Content-Type: application/zip" --data-binary @exports_brevo_JJMMAA.zip`
   - `slack_complete_file_upload` avec `channel_id = C0BNJUMF4H2` et le commentaire « Exports Brevo des 9 comptes — relevé du JJ.MM.AAAA ».

4. **Verdict** (message Slack dans le canal `C0BNJUMF4H2`), à partir de `_rapport_extraction.json` :
   - en tête : ✅ si les 9 comptes sont extraits, ⚠️ si au moins un club a une anomalie bloquante ou a échoué, ❌ si le zip n'a pas pu être publié ;
   - tableau par club : contacts totaux, exploitables, engagés, actif total, non-engagés, billetterie, campagnes ;
   - anomalies bloquantes : club en échec et pourquoi, segment introuvable (sauf LS et SANTE, voir plus bas), contrôle « exploitables = segment Brevo » ou « engagés ⊆ actif total » en échec, contacts hors base totale ;
   - durée et nombre d'appels API par club.
   Nombres en format suisse : espace pour les milliers (35 690).

## À savoir pour lire le rapport

- LS n'a ni segment `CMON-Actifs-6m` (ACTIF TOTAL) ni segment billetterie : c'est normal, à mentionner sans alerte.
- Quelques contacts à la fois engagés et non-engagés : chevauchement connu des segments Brevo, information seulement.
- SANTE (compte santé, ajouté le 05.11.2026) n'est pas un club : pas d'attribut NPA (le code postal vient de `_DETECTED_POSTALCODE`, détecté par Brevo) et ses segments n'ont pas encore été vérifiés. Un segment SANTE introuvable est à mentionner sans alerte, avec son nom, pour qu'on l'ajuste. Si le rapport de SANTE contient `segments_disponibles`, recopie dans le verdict la liste complète de ces noms de segments (tels quels), pour qu'on choisisse les bons.
