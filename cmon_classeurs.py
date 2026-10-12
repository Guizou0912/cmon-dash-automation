#!/usr/bin/env python3
"""Classeurs Looker du Dash Performance (§1-2 de PROMPT_MAJ_DASHBOARD_PERFORMANCE.md), au format du relevé 210926.

    python cmon_classeurs.py [--current 121026] [--history 290926]

Entrée  : CSV extraits par cmon_brevo.py dans Fichier ZIP _\\<JJMMAA>\\, delivrabilite.json du même dossier.
Sorties : <JJMMAA>\\A UPLOADER\\CMON_DATA_<CLUB>_DASH_PERFORMANCE.xlsx (8)
          <JJMMAA>\\NON UPLOADE - calculs et notes\\<CLUB> - Export du … - Taux NL.xlsx
L'historique du Résumé (colonnes K→AK) est recopié depuis le classeur du relevé --history, puis la ligne du relevé est ajoutée.
"""
import argparse
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cmon_brevo import BASE, EXPECTED_ATTRS, find_file, read_csv, relevé_dirs  # noqa: E402
from cmon_kpi_html import NL_CATS, nl_cat, rate  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

COLS_13 = ["EMAIL", "DOUBLE_OPT-IN", "OPT_IN", "SMS", "PRENOM", "NOM", "CMON_SCORE_26_27",
           "SOURCE_ACQUISITION", "CMON_SCORE", "NPA", "ANNIVERSAIRE", "ADDED_TIME", "MODIFIED_TIME"]
COLS_15 = ["EMAIL", "DOUBLE_OPT-IN", "OPT_IN", "NOM", "PRENOM", "SMS", "CMON_SCORE_26_27", "CATÉGORIE DE FAN (26-27)",
           "SOURCE_ACQUISITION", "CMON_SCORE", "CATÉGORIE DE FAN (all-time)", "ANNIVERSAIRE", "NPA", "ADDED_TIME", "MODIFIED_TIME"]
SHEETS = [("Contacts totaux", "Contacts totaux"), ("Contacts exploitables", "Contacts exploitables"),
          ("Contacts engagés", "Contacts engagés"), ("Contacts non-engagés", "Contacts non-engagés"),
          ("Billetterie Active Saison 26-27", "Billetterie Active Saison 26-27")]
RESUME_HDR = ["Contacts totaux", "Contacts exploitables", "Taux d'exploitabilité", "Taux de complétion (PRENOM)", "Taux de complétion (NOM)",
              "Taux de complétion (EMAIL)", "Taux de complétion (ANNIVERSAIRE)", "Taux de complétion (NPA)", "Taux de complétion (SMS)",
              "Taux de complétion global", "Date", "Nombre de contacts exploitables", "Nouveaux contacts acquis (exploitables)",
              "Nombre de contacts engagés", "Nouveaux contacts acquis (engagés)", "Nombre de contacts non-engagés", "Nouveaux contacts (non-engagés)",
              'Nombre de contacts dans le segment "Billetterie Active Saison 26-27"', "Nouveaux contacts acquis (Billetterie 26-27)",
              "Catégorie de fan", "Nombre de contacts par catégorie (scoring all-time)", "Nombre de contacts par catégorie (scoring 26-27)",
              "Canal d'acquisition", "Nombre de contacts par canal", "Score de délivrabilité",
              "Taux d'ouverture AVM", "Taux d'ouverture AVM Programme", "Taux d'ouverture APM", "Taux d'ouverture Autres NL",
              "Taux de clic AVM", "Taux de clic AVM Programme", "Taux de clic APM", "Taux de clic Autres NL",
              "Taux de désinscription AVM", "Taux de désinscription AVM Programme", "Taux de désinscription APM", "Taux de désinscription Autres NL"]
FAN_CATS = ["New Lead Fan", "Warm Fan", "Qualified Fan", "Sales Qualified Fan", "Super Fan"]
CANAUX = ["Newsletters (inscription)", "Fan Engagement (concours)", "Billetterie"]
CAMPAIGN_RATES = {"Non delivered rate", "Trackable open rate", "Click rate", "Click-to-Open rate", "Unsubscription rate",
                  "Delivered rate", "Hard Bounces rate", "Soft Bounces rate", "Complaints rate"}
CAMPAIGN_INTS = {"Campaign ID", "Sent", "Non delivered", "Hard bounces", "Soft bounces", "Delivered", "Total opens", "Opens",
                 "Apple MPP Opens", "Total clicked", "Clicked", "Unsubscribed", "Complaints"}
HISTORY_COLS = [11, 12, 14, 16, 18] + list(range(25, 38))  # K, L, N, P, R, Y→AK : la série empilée
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

HEAD_FONT = Font(bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
HEAD_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
DT_FMT = "yyyy-mm-dd h:mm:ss"


def header(ws, cols, width):
    ws.append(cols)
    for i, c in enumerate(ws[1], 1):
        c.font, c.fill, c.alignment = HEAD_FONT, HEAD_FILL, HEAD_ALIGN
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    ws.freeze_panes = "A2"


def to_date(v):
    try:
        return datetime.strptime(v, "%d-%m-%Y") if v else None
    except ValueError:
        return None


def to_int(v):
    try:
        return int(float(str(v).replace(",", "."))) if v not in (None, "") else None
    except ValueError:
        return None


def map_row(r, club):
    """Ligne CSV Brevo → valeurs des 13 colonnes (mapping d'attributs du club, §1)."""
    m = EXPECTED_ATTRS[club]
    sms = r.get("SMS") or ""
    if club == "FOXES" and not sms:  # FOXES : SMS vide à l'export, rempli depuis TELEPHONE_PORTABLE
        sms = r.get("TELEPHONE_PORTABLE") or ""
    return {
        "EMAIL": r.get("EMAIL") or None, "DOUBLE_OPT-IN": r.get("DOUBLE_OPT-IN") or None, "OPT_IN": r.get("OPT_IN") or None,
        "SMS": sms or None, "PRENOM": r.get("PRENOM") or None, "NOM": r.get("NOM") or None,
        "CMON_SCORE_26_27": to_int(r.get(m["CMON_SCORE_26_27"])) if m["CMON_SCORE_26_27"] else None,
        "SOURCE_ACQUISITION": r.get("SOURCE_ACQUISITION") or None, "CMON_SCORE": to_int(r.get(m["CMON_SCORE"])),
        "NPA": r.get(m["NPA"]) or None, "ANNIVERSAIRE": to_date(r.get(m["ANNIVERSAIRE"])),
        "ADDED_TIME": to_date(r.get("ADDED_TIME")), "MODIFIED_TIME": to_date(r.get("MODIFIED_TIME")),
    }


def write_contacts(ws, rows, club, cols):
    header(ws, cols, 22)
    date_cols = [i for i, c in enumerate(cols, 1) if c in ("ANNIVERSAIRE", "ADDED_TIME", "MODIFIED_TIME")]
    for n, r in enumerate(rows, 2):
        v = map_row(r, club)
        if cols is COLS_15:
            v["CATÉGORIE DE FAN (26-27)"] = f'=IF(G{n}>=149,"Super Fan",IF(G{n}>=99,"Sales Qualified Fan",IF(G{n}>=69,"Qualified Fan",IF(G{n}>=24,"Warm Fan","New Lead Fan"))))'
            v["CATÉGORIE DE FAN (all-time)"] = f'=IF(J{n}>=149,"Super Fan",IF(J{n}>=99,"Sales Qualified Fan",IF(J{n}>=69,"Qualified Fan",IF(J{n}>=24,"Warm Fan","New Lead Fan"))))'
        ws.append([v[c] for c in cols])
        for i, c in enumerate(cols, 1):  # un texte saisi "=…" ne doit jamais devenir une formule
            if c not in ("CATÉGORIE DE FAN (26-27)", "CATÉGORIE DE FAN (all-time)") and isinstance(v[c], str) and v[c].startswith("="):
                ws.cell(n, i).data_type = "s"
        for i in date_cols:
            ws.cell(n, i).number_format = DT_FMT
    return len(rows) + 1  # dernière ligne


def nl_rates(rows):
    out = {}
    for cat in NL_CATS:
        rs = [r for r in rows if nl_cat(r["Campaign Name"]) == cat]
        dlv = sum(int(r["Delivered"] or 0) for r in rs)
        out[cat] = None if not rs or not dlv else (sum(int(r["Opens"] or 0) for r in rs) / dlv,
                                                    sum(int(r["Clicked"] or 0) for r in rs) / dlv,
                                                    sum(rate(r["Unsubscription rate"]) for r in rs) / len(rs))
    return out


def history_rows(path):
    """Lignes K→AK du Résumé d'un classeur précédent (valeurs uniquement, pas les formules de delta)."""
    if not path or not path.exists():
        return []
    ws = openpyxl.load_workbook(path)["Résumé"]
    out = []
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 11).value in (None, ""):
            continue
        out.append({c: ws.cell(r, c).value for c in HISTORY_COLS})
    return out


def build_resume(ws, T, E, history, new_row):
    header(ws, RESUME_HDR, 24)
    q = "'Contacts totaux'"
    x = "'Contacts exploitables'"
    ws["A2"] = f"=COUNTA({q}!M2:M{T})"
    ws["B2"] = f"=COUNTA({x}!O2:O{E})"
    ws["C2"] = "=B2/A2"
    for col, src in zip("DEFGHI", "EDALMF"):
        ws[f"{col}2"] = f"=COUNTA({x}!{src}2:{src}{E}) / COUNTA({x}!O2:O{E})"
    ws["J2"] = "=AVERAGE(D2:I2)"
    for col in "CDEFGHIJ":
        ws[f"{col}2"].number_format = "0.00%"
    for i, cat in enumerate(FAN_CATS, 2):
        ws[f"T{i}"] = cat
        ws[f"U{i}"] = f'=COUNTIF({x}!K2:K{E},"{cat}")'
        ws[f"V{i}"] = f'=COUNTIF({x}!H2:H{E},"{cat}")'
    for i, canal in enumerate(CANAUX, 2):
        ws[f"W{i}"] = canal
        ws[f"X{i}"] = f'=COUNTIF({x}!I2:I{E},"{canal}")'
    ws["W5"] = "Non renseigné"
    ws["X5"] = f"=COUNTBLANK({x}!I2:I{E})"
    rows = [h for h in history if h[11] and (not isinstance(h[11], datetime) or h[11].date() != new_row[11].date())] + [new_row]
    for i, h in enumerate(rows, 2):
        for c in range(11, 38):
            if c not in HISTORY_COLS:  # deltas (M,O,Q,S) et blocs T→X : formules du relevé courant, jamais recopiées
                continue
            v = h.get(c)
            cell = ws.cell(i, c)
            cell.value = v
            if c == 11:
                cell.number_format = "DD/MM/YYYY"
            elif c >= 26 and v is not None:
                cell.number_format = "0.00%"
    for r in range(3, 41):
        for col, src in (("M", "L"), ("O", "N"), ("Q", "P"), ("S", "R")):
            ws[f"{col}{r}"] = f'=IF(OR({src}{r}="",{src}{r - 1}=""),"",{src}{r}-{src}{r - 1})'
    return len(rows)


def build_nl(path, rows):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    from cmon_brevo import CAMPAIGN_COLS
    for cat in NL_CATS:
        ws = wb.create_sheet(cat)
        header(ws, CAMPAIGN_COLS, 22)
        rs = [r for r in rows if nl_cat(r["Campaign Name"]) == cat]
        if not rs:
            ws["B7"] = "Aucune campagne de ce type sur la période"
            continue
        for n, r in enumerate(rs, 2):
            for i, col in enumerate(CAMPAIGN_COLS, 1):
                v = r[col]
                cell = ws.cell(n, i)
                if col in CAMPAIGN_RATES:
                    cell.value, cell.number_format = rate(v), "0.00%"
                elif col in CAMPAIGN_INTS:
                    cell.value = to_int(v)
                elif col == "Sending date":
                    cell.value, cell.number_format = datetime.strptime(v[:19], "%Y-%m-%d %H:%M:%S"), "DD/MM/YYYY HH:MM"
                else:
                    cell.value = v
        last = len(rs) + 1
        ws[f"B{last + 6}"], ws[f"C{last + 6}"] = "Taux d'ouverture", f"=SUM(N2:N{last})/SUM(L2:L{last})"
        ws[f"B{last + 7}"], ws[f"C{last + 7}"] = "Taux de clic", f"=SUM(R2:R{last})/SUM(L2:L{last})"
        ws[f"B{last + 8}"], ws[f"C{last + 8}"] = "Taux de désinscription", f"=AVERAGE(V2:V{last})"
        for k in range(6, 9):
            ws[f"C{last + k}"].number_format = "0.00%"
    wb.save(path)


def fr_period(a, b):
    return f"du {a.day} {MOIS[a.month - 1]}{'' if a.year == b.year else ' ' + str(a.year)} au {b.day} {MOIS[b.month - 1]} {b.year}"


def build_club(club, cur_dir, hist_dir, releve_date, deliv, etat=None):
    out_dir, nl_dir = cur_dir / "A UPLOADER", cur_dir / "NON UPLOADE - calculs et notes"
    out_dir.mkdir(exist_ok=True)
    nl_dir.mkdir(exist_ok=True)
    data = {}
    for _, kind in SHEETS:
        f = find_file(cur_dir, club, kind)
        data[kind] = read_csv(f)[1] if f else None

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    last = {}
    for title, kind in SHEETS:
        ws = wb.create_sheet(title)
        rows = data[kind] or []
        last[kind] = write_contacts(ws, rows, club, COLS_15 if kind == "Contacts exploitables" else COLS_13)

    camp_file = find_file(cur_dir, club, "campaigns")
    camps = read_csv(camp_file)[1] if camp_file else []
    rates = nl_rates(camps)
    new_row = {c: None for c in range(11, 38)}
    new_row[11] = releve_date
    new_row[12] = len(data["Contacts exploitables"] or [])
    new_row[14] = len(data["Contacts engagés"]) if data["Contacts engagés"] is not None else None
    new_row[16] = len(data["Contacts non-engagés"]) if data["Contacts non-engagés"] is not None else None
    new_row[18] = len(data["Billetterie Active Saison 26-27"]) if data["Billetterie Active Saison 26-27"] is not None else None
    new_row[25] = (deliv or {}).get("score")
    for j, cat in enumerate(NL_CATS):  # vide (jamais 0) si aucune campagne
        if rates[cat]:
            new_row[26 + j], new_row[30 + j], new_row[34 + j] = (round(v, 4) for v in rates[cat])

    if etat is not None:
        from cmon_etat import history_from_etat
        history = history_from_etat(etat, club)
        hist_file = Path(f"etat {etat['releve']}")
    elif hist_dir is not None:
        hist_file = hist_dir / "A UPLOADER" / f"CMON_DATA_{club}_DASH_PERFORMANCE.xlsx"
        history = history_rows(hist_file)
    else:  # ni état ni classeur précédent : le Résumé démarre avec la seule ligne du relevé
        hist_file, history = Path("aucun historique"), []
    n_hist = build_resume(wb.create_sheet("Résumé"), last["Contacts totaux"], last["Contacts exploitables"], history, new_row)
    target = out_dir / f"CMON_DATA_{club}_DASH_PERFORMANCE.xlsx"
    wb.save(target)

    nl_target = None
    if camp_file:
        a, b = camp_file.stem.split("campaigns-")[-1].strip().split("_")
        nl_target = nl_dir / f"{club} - Export {fr_period(datetime.fromisoformat(a), datetime.fromisoformat(b))} - Taux NL.xlsx"
        build_nl(nl_target, camps)
    return {"classeur": target.name, "lignes_historique": n_hist, "historique_depuis": hist_file.name if etat is not None else (hist_file.parent.parent.name if hist_file.exists() else None),
            "taux_nl": nl_target.name if nl_target else None, "volumes": {k: (len(v) if v is not None else None) for k, v in data.items()},
            "delivrabilite": new_row[25], "nl": {c: (None if not v else [round(x, 4) for x in v]) for c, v in rates.items()}}


def verify(path):
    """Contrôle sans LibreOffice : formules bien formées, références de plage cohérentes, aucune valeur d'erreur écrite."""
    import re
    wb = openpyxl.load_workbook(path)
    issues, n = [], 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, str) and v.startswith("="):
                    n += 1
                    if v.count("(") != v.count(")") or v.count('"') % 2:
                        issues.append(f"{ws.title}!{c.coordinate} parenthèses/guillemets")
                    for sheet in re.findall(r"'([^']+)'!", v):
                        if sheet not in wb.sheetnames:
                            issues.append(f"{ws.title}!{c.coordinate} onglet inconnu {sheet}")
                elif ws.title == "Résumé" and isinstance(v, str) and v.startswith("#"):  # dans les onglets contacts, "#…" est une saisie
                    issues.append(f"{ws.title}!{c.coordinate} valeur d'erreur {v}")
    return n, issues


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", default=datetime.now().strftime("%d%m%y"))
    ap.add_argument("--history", default=None, help="relevé dont on reprend l'historique du Résumé (défaut : le plus récent qui a un dossier A UPLOADER)")
    ap.add_argument("--club", action="append")
    ap.add_argument("--etat", help="etat_dash_<JJMMAA>.json de la semaine précédente (routine cloud)")
    a = ap.parse_args()
    root = BASE / "Fichier ZIP _"
    cur_dir = root / a.current
    etat = None
    if a.etat:
        from cmon_etat import load
        etat = load(a.etat)
    hist_dir = root / a.history if a.history else next((d for d in relevé_dirs() if d != cur_dir and (d / "A UPLOADER").exists()), None)
    releve_date = datetime.strptime(a.current, "%d%m%y")
    deliv_file = cur_dir / "delivrabilite.json"
    deliv = json.loads(deliv_file.read_text(encoding="utf-8")) if deliv_file.exists() else {}
    report = {}
    for club in (c.upper() for c in a.club) if a.club else EXPECTED_ATTRS:
        if not find_file(cur_dir, club, "Contacts totaux"):
            continue
        r = build_club(club, cur_dir, hist_dir, releve_date, deliv.get(club), etat)
        n, issues = verify(cur_dir / "A UPLOADER" / r["classeur"])
        r["formules"], r["problemes_formules"] = n, issues
        report[club] = r
        print(f"[{club}] {r['classeur']} · historique {r['lignes_historique']} lignes · {n} formules · {len(issues)} problème(s)", flush=True)
    (cur_dir / "_rapport_classeurs.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
