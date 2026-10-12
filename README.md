# cmon-dash-automation

Mise à jour hebdomadaire du Dash Performance C'mon Sports (8 clubs) à partir de l'API Brevo.

| Script | Rôle |
|---|---|
| `cmon_brevo.py --extract` | extrait les 8 comptes Brevo (contacts, segments par nom, campagnes 3 mois) en CSV au format des exports manuels |
| `cmon_classeurs.py` | construit les 8 classeurs Looker `CMON_DATA_<CLUB>_DASH_PERFORMANCE.xlsx` et les classeurs Taux NL |
| `cmon_kpi_html.py` | page KPI récapitulative 8 clubs |
| `cmon_etat.py` | fichier d'état hebdomadaire (agrégats + historique du Résumé) relu la semaine suivante |

La routine cloud suit `ROUTINE.md`. Clés : variables d'environnement `BREVO_KEY_<CLUB>` de l'environnement cloud, ou `brevo_keys.json` en local (jamais commité). Ce dépôt ne contient que du code.
