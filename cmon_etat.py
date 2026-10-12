#!/usr/bin/env python3
"""Fichier d'état hebdomadaire : ce que la routine cloud doit savoir de la semaine précédente.

    python cmon_etat.py --current 121026            → Fichier ZIP _\\121026\\etat_dash_121026.json

Contenu, par club : agrégats KPI (aucune donnée personnelle), score de délivrabilité, historique du Résumé (colonnes K→AK).
La semaine suivante, cmon_kpi_html.py et cmon_classeurs.py le relisent avec --etat au lieu des CSV et classeurs précédents.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cmon_brevo import BASE, EXPECTED_ATTRS, find_file  # noqa: E402

DROP = {"ids", "src", "src_prev", "new_prev"}


def _enc(v):
    return v.isoformat() if isinstance(v, datetime) else v


def _dec_row(row):
    out = {}
    for k, v in row.items():
        c = int(k)
        out[c] = datetime.fromisoformat(v) if c == 11 and isinstance(v, str) else v
    return out


def load(path):
    e = json.loads(Path(path).read_text(encoding="utf-8"))
    for club in e["clubs"].values():
        club["resume_history"] = [_dec_row(r) for r in club.get("resume_history", [])]
    return e


def restore(path):
    """Routine cloud : recrée delivrabilite_calibration.csv depuis l'état de la semaine précédente."""
    from cmon_kpi_html import CALIB
    e = json.loads(Path(path).read_text(encoding="utf-8"))
    if e.get("calibration_csv") and not CALIB.exists():
        CALIB.write_text(e["calibration_csv"], encoding="utf-8")
    return e["releve"]


def prev_from_etat(etat, club):
    """Objet « relevé précédent » attendu par cmon_kpi_html, reconstruit depuis l'état."""
    c = etat["clubs"].get(club)
    if not c:
        return None
    return {"folder": etat["releve"], "files": {}, "k": dict(c["kpi"]), "deliv": {"officiel": c.get("delivrabilite")},
            "Contacts totaux": None, "campaigns": None}


def history_from_etat(etat, club):
    c = etat["clubs"].get(club) if etat else None
    return list(c["resume_history"]) if c else []


def export(cur_name):
    import openpyxl
    from cmon_kpi_html import load_relevé
    from cmon_classeurs import history_rows
    cur = BASE / "Fichier ZIP _" / cur_name
    deliv_file = cur / "delivrabilite.json"
    deliv = json.loads(deliv_file.read_text(encoding="utf-8")) if deliv_file.exists() else {}
    out = {"releve": cur_name, "genere_le": datetime.now().isoformat(timespec="seconds"), "clubs": {}}
    for club in EXPECTED_ATTRS:
        if not find_file(cur, club, "Contacts totaux"):
            continue
        k = {key: val for key, val in load_relevé(cur, club)["k"].items() if key not in DROP}
        hist = history_rows(cur / "A UPLOADER" / f"CMON_DATA_{club}_DASH_PERFORMANCE.xlsx")
        out["clubs"][club] = {"kpi": k, "delivrabilite": deliv.get(club),
                              "resume_history": [{str(c): _enc(v) for c, v in r.items()} for r in hist]}
    from cmon_kpi_html import CALIB
    if CALIB.exists():
        out["calibration_csv"] = CALIB.read_text(encoding="utf-8")
    path = cur / f"etat_dash_{cur_name}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", default=datetime.now().strftime("%d%m%y"))
    ap.add_argument("--restore", help="etat_dash_<JJMMAA>.json à relire (recrée le journal de calibration)")
    a = ap.parse_args()
    if a.restore:
        print("état restauré, relevé précédent :", restore(a.restore))
        return
    p = export(a.current)
    print(p, f"{p.stat().st_size} octets")


if __name__ == "__main__":
    main()
