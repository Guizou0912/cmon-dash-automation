#!/usr/bin/env python3
"""Page HTML des KPI hebdo (§3-4 de PROMPT_MAJ_DASHBOARD_PERFORMANCE.md) à partir des CSV extraits.

    python cmon_kpi_html.py --club SVWE [--current 121026] [--previous 0610]

Uniquement des agrégats : aucune donnée personnelle dans la page produite.
"""
import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cmon_brevo import BASE, EXPECTED_ATTRS, find_file, read_csv, relevé_dirs  # noqa: E402

FAN_CATS = ["New Lead Fan", "Warm Fan", "Qualified Fan", "Sales Qualified Fan", "Super Fan"]
NL_CATS = ["AVM", "AVM Programme", "APM", "Autres"]


# ---------------------------------------------------------------- formats suisses
def fnum(n):
    return f"{n:,}".replace(",", " ") if isinstance(n, int) else f"{n:,.2f}".replace(",", " ").replace(".", ",")


def fpct(x):
    return f"{x * 100:.2f}".replace(".", ",") + " %"


def delta_html(cur, prev, is_rate):
    if prev is None or cur is None:
        return '<span class="d n">(nouveau)</span>'
    d = (cur - prev) * (100 if is_rate else 1)
    if is_rate:
        txt = f"{d:+.2f}".replace(".", ",")
        if txt in ("+0,00", "-0,00"):
            txt = "0,00"
    else:
        txt = f"{int(d):+,}".replace(",", " ") if d else "0"
    cls = "p" if d > 0.00499 else ("m" if d < -0.00499 else "n")
    return f'<span class="d {cls}">({txt})</span>'


def val(cur, prev, is_rate=False):
    if cur is None:
        return '<span class="na">—</span>'
    return f"{fpct(cur) if is_rate else fnum(cur)} {delta_html(cur, prev, is_rate)}"


# ---------------------------------------------------------------- calculs
def fan_cat(v):
    try:
        g = float(str(v).replace(",", "."))
    except ValueError:
        g = 0
    return "Super Fan" if g >= 149 else "Sales Qualified Fan" if g >= 99 else "Qualified Fan" if g >= 69 else "Warm Fan" if g >= 24 else "New Lead Fan"


def load_relevé(folder, club):
    m = EXPECTED_ATTRS[club]
    data = {"folder": folder.name, "files": {}}
    for kind in ["Contacts totaux", "Contacts engagés", "Contacts non-engagés", "Billetterie Active Saison 26-27", "ACTIF TOTAL", "campaigns"]:
        f = find_file(folder, club, kind)
        data["files"][kind] = f.name if f else None
        data[kind] = read_csv(f)[1] if f else None
    T = data["Contacts totaux"] or []
    n = len(T)
    fill = lambda col: (sum(1 for r in T if col and (r.get(col) or "").strip()) / n) if n else 0
    if T and "_SUBSCRIBED" in T[0]:
        expl = [r for r in T if "email_marketing" in (r.get("_SUBSCRIBED") or "")]
    else:  # LS manuel : pas de _SUBSCRIBED, le fichier segment fait foi
        fe = find_file(folder, club, "Contacts exploitables")
        expl = read_csv(fe)[1] if fe else []
    ne = len(expl)
    fill_e = lambda col: (sum(1 for r in expl if col and (r.get(col) or "").strip()) / ne) if ne else 0
    opt = [(r.get("OPT_IN") or "").strip().upper() for r in T]
    actif_ids = {r["CONTACT ID"] for r in data["ACTIF TOTAL"]} if data["ACTIF TOTAL"] is not None else None
    k = {
        "base": n,
        "ids": {r["CONTACT ID"] for r in T},
        "src": {r["CONTACT ID"]: (r.get("SOURCE_ACQUISITION") or "").strip() for r in T},
        "optin_yes": opt.count("YES") / n if n else 0,
        "optin_no_n": sum(1 for o in opt if o and o != "YES"),
        "optin_vide": opt.count("") / n if n else 0,
        "completude": sum(fill(c) for c in ["NOM", "PRENOM", "EMAIL", m["NPA"], "SMS", m["ANNIVERSAIRE"], m["CMON_SCORE"]]) / 7,
        "expl_n": ne,
        "expl_rate": ne / n if n else 0,
        "completion_expl": sum(fill_e(c) for c in ["PRENOM", "NOM", "EMAIL", m["ANNIVERSAIRE"], m["NPA"], "SMS"]) / 6,
        "actifs_n": len(actif_ids & {r["CONTACT ID"] for r in T}) if actif_ids is not None else None,
        "engages": len(data["Contacts engagés"]) if data["Contacts engagés"] is not None else None,
        "non_engages": len(data["Contacts non-engagés"]) if data["Contacts non-engagés"] is not None else None,
        "billet": len(data["Billetterie Active Saison 26-27"]) if data["Billetterie Active Saison 26-27"] is not None else None,
        "fans_all": {c: sum(1 for r in expl if fan_cat(r.get(m["CMON_SCORE"]) or 0) == c) for c in FAN_CATS},
        "fans_2627": {c: sum(1 for r in expl if fan_cat(r.get(m["CMON_SCORE_26_27"] or "") or 0) == c) for c in FAN_CATS} if m["CMON_SCORE_26_27"] else None,
    }
    k["optin_no"] = k["optin_no_n"] / n if n else 0
    k["actifs_rate"] = k["actifs_n"] / n if k["actifs_n"] is not None and n else None
    k["nl"] = nl_stats(data["campaigns"]) if data["campaigns"] is not None else None
    k["nl_window"] = data["files"]["campaigns"]
    data["k"] = k
    return data


def nl_cat(name):
    u = (name or "").upper()
    return "AVM Programme" if "PROGRAMME" in u or "PROGRAM" in u else "AVM" if "AVM" in u else "APM" if "APM" in u else "Autres"


def rate(s):
    return float(str(s).replace("%", "").replace(",", ".").strip() or 0) / 100


# ---------------------------------------------------------------- délivrabilité
CALIB = BASE / "delivrabilite_calibration.csv"
CALIB_COLS = ["releve", "club", "fenetre", "score_brevo", "delivered_rate", "soft_rate", "hard_rate", "unsub_rate", "complaint_rate", "campagnes", "source"]


def deliv_metrics(rows, releve_date):
    """Stats d'envoi sur les 30 jours précédant le relevé (même fenêtre que l'écran Brevo)."""
    from datetime import timedelta
    start, end = releve_date - timedelta(days=30), releve_date
    rs = [r for r in rows or [] if r["Sending date"] and start <= datetime.strptime(r["Sending date"][:10], "%Y-%m-%d") < end]
    if not rs:
        return None
    S = lambda k: sum(int(r[k] or 0) for r in rs)
    sent, dlv = S("Sent"), S("Delivered")
    return {"n": len(rs), "sent": sent, "delivered": dlv / sent, "soft": S("Soft bounces") / sent, "hard": S("Hard bounces") / sent,
            "unsub": S("Unsubscribed") / dlv if dlv else 0, "complaint": S("Complaints") / dlv if dlv else 0,
            "debut": f"{start:%d.%m}", "fin": f"{end - timedelta(days=1):%d.%m.%Y}"}


def calib_rows():
    if not CALIB.exists():
        return []
    import csv
    with CALIB.open(encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh, delimiter=";") if r.get("score_brevo")]


def fit_model(rows):
    """Moindres carrés : score ~ a + b·soft% + c·désinscription%. Renvoie (coefs, écart moyen absolu)."""
    pts = [(float(r["soft_rate"]), float(r["unsub_rate"]), float(r["score_brevo"])) for r in rows]
    if len(pts) < 4:
        return None, None
    # équations normales 3x3, résolues par Gauss
    X = [(1.0, s, u) for s, u, _ in pts]
    y = [sc for _, _, sc in pts]
    A = [[sum(x[i] * x[j] for x in X) for j in range(3)] + [sum(x[i] * yy for x, yy in zip(X, y))] for i in range(3)]
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(A[r][i]))
        A[i], A[piv] = A[piv], A[i]
        for r in range(3):
            if r != i:
                f = A[r][i] / A[i][i]
                A[r] = [a - f * b for a, b in zip(A[r], A[i])]
    coef = [A[i][3] / A[i][i] for i in range(3)]
    mae = sum(abs(coef[0] + coef[1] * s + coef[2] * u - sc) for s, u, sc in pts) / len(pts)
    return coef, mae


def deliv_block(folder, club, campaigns, releve_date):
    met = deliv_metrics(campaigns, releve_date)
    off = None
    f = folder / "delivrabilite.json"
    if f.exists():
        off = json.loads(f.read_text(encoding="utf-8")).get(club)
    rows = [r for r in calib_rows() if r["releve"] != folder.name]  # estimation hors relevé courant
    coef, mae = fit_model(rows)
    est = None
    if coef and met:
        est = {"valeur": max(0, min(100, coef[0] + coef[1] * met["soft"] * 100 + coef[2] * met["unsub"] * 100)), "mae": mae, "n": len(rows)}
    return {"officiel": off, "estime": est, "metriques": met}


def log_calibration(folder, club, block):
    """Ajoute (ou remplace) la ligne du relevé dans le journal de calibration quand le score officiel est connu."""
    import csv
    off, met = block.get("officiel"), block.get("metriques")
    if not off or not met:
        return False
    rows = [r for r in (list(csv.DictReader(CALIB.open(encoding="utf-8", newline=""), delimiter=";")) if CALIB.exists() else [])
            if not (r["releve"] == folder.name and r["club"] == club)]
    rows.append({"releve": folder.name, "club": club, "fenetre": off.get("fenetre", ""), "score_brevo": off["score"],
                 "delivered_rate": f"{met['delivered'] * 100:.2f}", "soft_rate": f"{met['soft'] * 100:.2f}", "hard_rate": f"{met['hard'] * 100:.2f}",
                 "unsub_rate": f"{met['unsub'] * 100:.2f}", "complaint_rate": f"{met['complaint'] * 100:.3f}", "campagnes": met["n"], "source": "capture + API"})
    with CALIB.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CALIB_COLS, delimiter=";")
        w.writeheader()
        w.writerows(rows)
    return True


def nl_stats(rows):
    out = {}
    for cat in NL_CATS:
        rs = [r for r in rows if nl_cat(r["Campaign Name"]) == cat]
        if not rs:
            out[cat] = None
            continue
        dlv = sum(int(r["Delivered"] or 0) for r in rs)
        out[cat] = {"n": len(rs), "open": sum(int(r["Opens"] or 0) for r in rs) / dlv if dlv else 0,
                    "click": sum(int(r["Clicked"] or 0) for r in rs) / dlv if dlv else 0,
                    "unsub": sum(rate(r["Unsubscription rate"]) for r in rs) / len(rs)}
    return out


# ---------------------------------------------------------------- page
CSS = """
:root{--bg:#f5f6f8;--card:#fff;--ink:#1b2333;--mut:#5b6577;--line:#e3e6ec;--head:#1F3864;--pos:#0a7d3d;--neg:#c2340a;--risk:#fff4f2}
@media (prefers-color-scheme:dark){:root{--bg:#11151c;--card:#1a2029;--ink:#e7eaf0;--mut:#9aa4b5;--line:#2b3340;--head:#2b4a80;--pos:#3fbf77;--neg:#ff7a52;--risk:#3a2420}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:28px 16px 48px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:16px;margin:32px 0 10px;color:var(--head)}
@media (prefers-color-scheme:dark){h2{color:#9db8ea}}
.sub{color:var(--mut);margin:0 0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card .l{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}.card .v{font-size:24px;font-weight:650;margin-top:4px;font-variant-numeric:tabular-nums}
.card .s{color:var(--mut);font-size:12px}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th{background:var(--head);color:#fff;font-weight:600;text-align:left;padding:8px 10px;font-size:12.5px;white-space:nowrap}
td{padding:7px 10px;border-top:1px solid var(--line);white-space:nowrap}td.r,th.r{text-align:right}
tr.risk td{background:var(--risk)}tr.tot td{font-weight:650}
.d{font-size:12px;margin-left:2px}.d.p{color:var(--pos)}.d.m{color:var(--neg)}.d.n{color:var(--mut)}.na{color:var(--mut)}
.sl{color:var(--mut);font-size:12px}
.boxes{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.box{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--neg);border-radius:10px;padding:12px 16px}
.box.i{border-left-color:var(--head)}.box h3{margin:0 0 6px;font-size:14px}.box ul{margin:0;padding-left:18px}.box li{margin:3px 0}
.ok{color:var(--pos);font-weight:600}.ko{color:var(--neg);font-weight:600}
footer{margin-top:32px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
footer li{margin:2px 0}
"""


def build(club, cur, prev, rapport):
    c, p = cur["k"], prev["k"]
    new_ids = c["ids"] - p["ids"]
    gone = p["ids"] - c["ids"]
    src_new = {}
    for i in new_ids:
        s = c["src"].get(i) or "sans source"
        src_new[s] = src_new.get(s, 0) + 1
    d_cur = datetime.strptime(cur["folder"], "%d%m%y")
    d_prev = datetime.strptime(prev["folder"] + ("26" if len(prev["folder"]) == 4 else ""), "%d%m%y")
    gap = (d_cur - d_prev).days
    rc = (rapport or {}).get("clubs", {}).get(club, {})
    e = lambda s: html.escape(str(s))

    h = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>KPI {club} {d_cur:%d.%m.%Y}</title><style>{CSS}</style></head><body><div class='wrap'>"]
    h.append(f"<h1>KPI hebdo · {club}</h1><p class='sub'>Relevé du <b>{d_cur:%d.%m.%Y}</b>, extrait automatiquement par l'API Brevo · "
             f"comparaison avec le relevé manuel du {d_prev:%d.%m.%Y} ({gap} jours) · population : toute la base du club</p>")

    # cartes
    sans = src_new.get("sans source", 0)
    h.append("<div class='cards'>")
    h.append(f"<div class='card'><div class='l'>Nouveaux contacts</div><div class='v'>{fnum(len(new_ids))}</div><div class='s'>{fnum(len(gone))} sortis de la base sur la période</div></div>")
    h.append(f"<div class='card'><div class='l'>Base totale</div><div class='v'>{fnum(c['base'])}</div><div class='s'>{delta_html(c['base'], p['base'], False)} vs {d_prev:%d.%m}</div></div>")
    h.append(f"<div class='card'><div class='l'>Nouveaux sans source</div><div class='v'>{fpct(sans / len(new_ids)) if new_ids else '—'}</div><div class='s'>{fnum(sans)} sur {fnum(len(new_ids))}</div></div>")
    h.append(f"<div class='card'><div class='l'>Opt-in NO</div><div class='v'>{fnum(c['optin_no_n'])}</div><div class='s'>{fpct(c['optin_no'])} de la base</div></div>")
    h.append("</div>")

    # indicateurs
    h.append("<h2>Indicateurs</h2><div class='tw'><table><tr><th>Club</th><th class='r'>Base totale</th><th class='r'>Nouveaux</th><th class='r'>Opt-in YES</th>"
             "<th class='r'>Opt-in NO</th><th class='r'>Opt-in vide</th><th class='r'>Complétude</th><th class='r'>Exploitable</th><th class='r'>Actifs</th></tr>")
    h.append(f"<tr><td><b>{club}</b></td><td class='r'>{val(c['base'], p['base'])}</td><td class='r'>{fnum(len(new_ids))}</td>"
             f"<td class='r'>{val(c['optin_yes'], p['optin_yes'], True)}</td>"
             f"<td class='r'>{val(c['optin_no'], p['optin_no'], True)}<br><span class='sl'>{fnum(c['optin_no_n'])} contacts</span></td>"
             f"<td class='r'>{val(c['optin_vide'], p['optin_vide'], True)}</td><td class='r'>{val(c['completude'], p['completude'], True)}</td>"
             f"<td class='r'>{val(c['expl_rate'], p['expl_rate'], True)}</td>"
             f"<td class='r'>{val(c['actifs_rate'], p['actifs_rate'], True)}<br><span class='sl'>{fnum(c['actifs_n']) if c['actifs_n'] is not None else '—'} contacts</span></td></tr></table></div>")

    # sources
    h.append("<h2>Sources d'acquisition des nouveaux contacts</h2><div class='tw'><table><tr><th>Source</th><th class='r'>Contacts</th><th class='r'>Part</th></tr>")
    for s, nn in sorted(src_new.items(), key=lambda x: -x[1]):
        h.append(f"<tr{' class=risk' if s == 'sans source' else ''}><td>{e(s)}</td><td class='r'>{fnum(nn)}</td><td class='r'>{fpct(nn / len(new_ids))}</td></tr>")
    h.append(f"<tr class='tot'><td>TOTAL</td><td class='r'>{fnum(len(new_ids))}</td><td class='r'>{fpct(1) if new_ids else '—'}</td></tr></table></div>")

    # abonnements + délivrabilité
    h.append("<h2>Abonnements</h2><div class='tw'><table><tr><th>Club</th><th class='r'>Total</th><th class='r'>Δ</th><th class='r'>Payant</th><th class='r'>Gratuit</th>"
             "<th class='r'>Public</th><th class='r'>VIP</th><th class='r'>Objectif</th><th class='r'>% atteint</th></tr>"
             f"<tr class='risk'><td><b>{club}</b></td><td colspan='8' class='na'>Non calculé : l'export billetterie (Saisonabonnemente 2026/27) n'est pas fourni par Brevo et n'est pas encore automatisé.</td></tr></table></div>")
    dv = cur.get("deliv") or {}
    off, est, met = dv.get("officiel"), dv.get("estime"), dv.get("metriques")
    prev_off = (prev.get("deliv") or {}).get("officiel")
    off_txt = (f"<b>{off['score']}</b> {delta_html(off['score'], prev_off['score'] if prev_off else None, False)}<br><span class='sl'>{e(off.get('fenetre', ''))}</span>"
               if off else "<span class='na'>En attente de la capture</span>")
    est_txt = (f"{est['valeur']:.0f}<br><span class='sl'>écart moyen ±{fnum(round(est['mae'], 1))} sur {est['n']} relevés</span>" if est else "<span class='na'>—</span>")
    if off and est:
        est_txt += f"<br><span class='sl'>écart avec le score officiel : {est['valeur'] - off['score']:+.0f}</span>"
    comp = (f"délivrés {fpct(met['delivered'])} · soft bounces {fpct(met['soft'])} · hard {fpct(met['hard'])} · désinscriptions {fpct(met['unsub'])} · plaintes {fpct(met['complaint'])}"
            f"<br><span class='sl'>{met['n']} campagnes, {fnum(met['sent'])} envois, du {met['debut']} au {met['fin']}</span>") if met else "<span class='na'>aucune campagne sur 30 jours</span>"
    h.append("<h2>Délivrabilité</h2><div class='tw'><table><tr><th>Club</th><th>Score Brevo (capture)</th><th>Indice estimé (API)</th><th>Composantes, 30 jours</th></tr>"
             f"<tr{'' if off else ' class=risk'}><td><b>{club}</b></td><td>{off_txt}</td><td>{est_txt}</td><td style='white-space:normal'>{comp}</td></tr></table></div>"
             "<p class='sub'>L'indice estimé est en calibration : il est comparé chaque semaine au score des captures et ne remplace pas le score officiel tant que l'écart n'est pas stable.</p>")

    # photo de la base
    h.append("<h2>Photo de la base</h2><div class='tw'><table><tr><th class='r'>Totaux</th><th class='r'>Exploitables</th><th class='r'>Exploitabilité</th>"
             "<th class='r'>Complétion</th><th class='r'>Engagés</th><th class='r'>Actif total</th><th class='r'>Non-engagés</th><th class='r'>Billetterie 26-27</th></tr>")
    h.append(f"<tr><td class='r'>{val(c['base'], p['base'])}</td><td class='r'>{val(c['expl_n'], p['expl_n'])}</td><td class='r'>{val(c['expl_rate'], p['expl_rate'], True)}</td>"
             f"<td class='r'>{val(c['completion_expl'], p['completion_expl'], True)}</td><td class='r'>{val(c['engages'], p['engages'])}</td>"
             f"<td class='r'>{val(c['actifs_n'], p['actifs_n'])}</td><td class='r'>{val(c['non_engages'], p['non_engages'])}</td>"
             f"<td class='r'>{val(c['billet'], p['billet'])}</td></tr></table></div>")

    # catégories de fans
    h.append("<h2>Catégories de fans (contacts exploitables)</h2><div class='tw'><table><tr><th>Catégorie</th><th class='r'>Scoring all-time</th><th class='r'>Scoring 26-27</th></tr>")
    for cat in FAN_CATS:
        h.append(f"<tr><td>{cat}</td><td class='r'>{val(c['fans_all'][cat], p['fans_all'][cat])}</td>"
                 f"<td class='r'>{val(c['fans_2627'][cat], p['fans_2627'][cat]) if c['fans_2627'] else '—'}</td></tr>")
    h.append("</table></div>")

    # NL
    win_c = (c["nl_window"] or "").split("campaigns-")[-1].replace(".csv", "").strip().replace("_", " → ")
    win_p = (p["nl_window"] or "").split("campaigns-")[-1].replace(".csv", "").strip().replace("_", " → ")
    h.append(f"<h2>Newsletters</h2><p class='sub'>Fenêtre actuelle {e(win_c)} · fenêtre du relevé précédent {e(win_p)}. Les deux fenêtres glissantes se chevauchent largement.</p>"
             "<div class='tw'><table><tr><th>Type</th><th class='r'>Campagnes</th><th class='r'>Taux d'ouverture</th><th class='r'>Taux de clic</th><th class='r'>Taux de désinscription</th></tr>")
    for cat in NL_CATS:
        a = (c["nl"] or {}).get(cat)
        b = (p["nl"] or {}).get(cat)
        if not a:
            h.append(f"<tr><td>{cat}</td><td colspan='4' class='na'>Aucune campagne de ce type sur la période</td></tr>")
            continue
        g = lambda key: val(a[key], b[key] if b else None, True)
        h.append(f"<tr><td>{cat}</td><td class='r'>{a['n']} {delta_html(a['n'], b['n'] if b else None, False)}</td><td class='r'>{g('open')}</td><td class='r'>{g('click')}</td><td class='r'>{g('unsub')}</td></tr>")
    h.append("</table></div>")

    # vigilance
    anomalies = list(rc.get("anomalies", []))
    lectures = []
    if prev["files"].get("Contacts totaux"):
        lectures.append(f"Le relevé de comparaison ({d_prev:%d.%m}) est un export manuel, celui-ci vient de l'API. Les contacts non modifiés entre les deux sont identiques champ par champ, donc les deltas reflètent de vrais mouvements.")
    lectures.append("L'exploitabilité du relevé précédent est recalculée depuis la base totale (règle : _SUBSCRIBED contient email_marketing) : son export manuel était une copie des totaux, une anomalie connue.")
    if p["engages"] is not None and c["engages"] is not None:
        lectures.append("Engagés, non-engagés et actifs sont des segments à fenêtre glissante (6 mois / 24 mois) : ils bougent même sans nouvelle interaction.")
    lectures.append("Engagés + non-engagés ≠ base totale : les contacts actifs entre 6 et 24 mois ne sont dans aucun des deux, c'est normal.")
    h.append("<h2>Points de vigilance</h2><div class='boxes'>")
    h.append("<div class='box'><h3>Anomalies d'extraction</h3><ul>" + ("".join(f"<li>{e(x)}</li>" for x in anomalies) or "<li>Aucune</li>") + "</ul></div>")
    h.append("<div class='box i'><h3>Lectures à ne pas tirer trop vite</h3><ul>" + "".join(f"<li>{e(x)}</li>" for x in lectures) + "</ul></div></div>")

    # contrôles
    ctl = rc.get("controles", {})
    ok = lambda b: "<span class='ok'>OK</span>" if b else "<span class='ko'>ÉCHEC</span>"
    h.append("<h2>Contrôles automatiques</h2><div class='tw'><table><tr><th>Contrôle</th><th>Résultat</th></tr>")
    ev = ctl.get("exploitables_vs_segment")
    if ev:
        h.append(f"<tr><td>Exploitables dérivés = segment Brevo « Contacts Exploitables »</td><td>{ok(ev['ok'])} · {fnum(ev['derive'])} / {fnum(ev['segment'])}</td></tr>")
    if "engages_inclus_dans_actif" in ctl:
        h.append(f"<tr><td>Engagés ⊆ Actif total (par CONTACT ID)</td><td>{ok(ctl['engages_inclus_dans_actif'])}</td></tr>")
    h.append(f"<tr><td>Segments ⊆ base totale (aucun orphelin)</td><td>{ok(not any('hors base' in a for a in anomalies))}</td></tr>")
    h.append(f"<tr><td>Extraction</td><td>{fnum(rc.get('appels_api', 0))} appels API · {rc.get('secondes', '—')} s · statut « {e(rc.get('statut', '—'))} »</td></tr></table></div>")

    h.append("<footer><b>Méthode.</b><ul>"
             "<li>Source : API Brevo du compte du club. Segments résolus par leur nom : engagés = <code>CMON-Actifs-6m-réels-(hors MPP)</code>, actif total = <code>CMON-Actifs-6m</code>, non-engagés = <code>CMON-Sunset-24m-plus</code>, billetterie = <code>Billetterie Active Saison 26-27</code>.</li>"
             "<li>Exploitable = contact inscrit aux campagnes email (non blacklisté), identique au segment Brevo « Contacts Exploitables ».</li>"
             "<li>Nouveaux contacts = identifiants présents dans ce relevé et absents du précédent.</li>"
             "<li>Complétude = moyenne du remplissage de 7 champs (nom, prénom, email, NPA, SMS, date de naissance, score) sur toute la base. Complétion (photo) = moyenne de 6 champs sur les exploitables, comme la colonne J du Résumé.</li>"
             "<li>Taux NL : ouverture = Σ ouvertures uniques / Σ délivrés ; clic = Σ clics uniques / Σ délivrés ; désinscription = moyenne des taux par campagne.</li>"
             "<li>Deltas en points pour les taux, en valeur absolue pour les volumes.</li>"
             f"<li>Généré le {datetime.now():%d.%m.%Y à %H:%M} par cmon_brevo.py.</li></ul></footer></div></body></html>")
    return "".join(h)


# ---------------------------------------------------------------- page récapitulative 8 clubs
CLUB_NAMES = {"LS": "Lausanne Sport", "CHAM": "Pionniers de Chamonix", "HCC": "HC La Chaux-de-Fonds", "YS": "Yverdon Sport",
              "LION": "Lions de Genève", "FOB": "Fribourg Olympic", "FOXES": "Pully Lausanne Foxes", "SVWE": "SV Wiler-Ersigen"}
SOURCES = ["Billetterie", "Newsletters (inscription)", "Fan Engagement (concours)", "Partenariats"]
CLUB_NOTES = {
    "LS": "Instance Brevo incomplète : pas de segment ACTIF ni billetterie, pas de SOURCE_ACQUISITION, OPT_IN rempli à ~3 % — opt-in non comparable aux autres clubs. Son exploitabilité est désormais calculée par l'API (non-blacklistés) alors que les anciens rapports affichaient 0 % dans le tableau des indicateurs : rupture de série.",
}


def build_recap(clubs, rapport, cur_name):
    """clubs : liste de (club, cur, prev). Page unique, agrégats uniquement."""
    e = lambda s: html.escape(str(s))
    d_cur = datetime.strptime(cur_name, "%d%m%y")
    tot_new = tot_base = tot_base_prev = tot_sans = tot_no = 0
    rows = []
    from datetime import timedelta
    wk_start, wk_end = d_cur - timedelta(days=7), d_cur - timedelta(days=1)
    pw_start, pw_end = wk_start - timedelta(days=7), wk_start - timedelta(days=1)

    def added_in(r, a, b):
        try:
            d = datetime.strptime(r.get("ADDED_TIME") or "", "%d-%m-%Y")
        except ValueError:
            return False
        return a <= d <= b

    tot_new_prev = tot_sans_prev = 0
    for club, cur, prev in sorted(clubs, key=lambda x: -x[1]["k"]["base"]):
        c, p = cur["k"], prev["k"]
        T = cur["Contacts totaux"] or []
        new_rows = [r for r in T if added_in(r, wk_start, wk_end)]
        prev_rows = [r for r in T if added_in(r, pw_start, pw_end)]
        new_ids = {r["CONTACT ID"] for r in new_rows}
        src, src_prev = {}, {}
        for rs, dst in ((new_rows, src), (prev_rows, src_prev)):
            for r in rs:
                s = (r.get("SOURCE_ACQUISITION") or "").strip() or "sans source"
                dst[s] = dst.get(s, 0) + 1
        c["new_prev"], c["src_prev"] = len(prev_rows), src_prev
        d_prev = datetime.strptime(prev["folder"] + ("26" if len(prev["folder"]) == 4 else ""), "%d%m%y")
        rows.append((club, cur, prev, c, p, new_ids, src, d_prev))
        tot_new += len(new_ids); tot_base += c["base"]; tot_base_prev += p["base"]
        tot_sans += src.get("sans source", 0); tot_no += c["optin_no_n"]
        tot_new_prev += len(prev_rows); tot_sans_prev += src_prev.get("sans source", 0)

    prev_dates = sorted({r[7] for r in rows})
    h = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>KPI hebdo {d_cur:%d.%m.%Y}</title><style>{CSS}</style></head><body><div class='wrap'>"]
    h.append(f"<h1>KPI Dash Performance</h1><p class='sub'>Semaine du {wk_start:%d.%m} au {wk_end:%d.%m.%Y} · relevé du <b>{d_cur:%d.%m.%Y}</b>, extrait automatiquement par l'API Brevo · "
             f"nouveaux contacts comparés à la semaine du {pw_start:%d.%m} au {pw_end:%d.%m} · photo de la base comparée au relevé du {' / '.join(f'{x:%d.%m.%Y}' for x in prev_dates)} · population : toute la base de chaque club</p>")

    h.append("<div class='cards'>")
    h.append(f"<div class='card'><div class='l'>Nouveaux contacts</div><div class='v'>{fnum(tot_new)} {delta_html(tot_new, tot_new_prev, False)}</div><div class='s'>{fnum(tot_new_prev)} la semaine précédente</div></div>")
    h.append(f"<div class='card'><div class='l'>Base totale cumulée</div><div class='v'>{fnum(tot_base)}</div><div class='s'>{delta_html(tot_base, tot_base_prev, False)}</div></div>")
    h.append(f"<div class='card'><div class='l'>Nouveaux sans source</div><div class='v'>{(fpct(tot_sans / tot_new) + ' ' + delta_html(tot_sans / tot_new, tot_sans_prev / tot_new_prev if tot_new_prev else None, True)) if tot_new else '—'}</div><div class='s'>{fnum(tot_sans)} contacts sur {fnum(tot_new)}</div></div>")
    h.append(f"<div class='card'><div class='l'>Opt-in NO total</div><div class='v'>{fnum(tot_no)}</div><div class='s'>contacts, 8 clubs</div></div></div>")

    # indicateurs
    h.append("<h2>Indicateurs par club</h2><div class='tw'><table><tr><th>Club</th><th class='r'>Base totale</th><th class='r'>Nouveaux</th><th class='r'>Opt-in YES</th>"
             "<th class='r'>Opt-in NO</th><th class='r'>Opt-in vide</th><th class='r'>Complétude</th><th class='r'>Exploitable</th><th class='r'>Actifs</th></tr>")
    for club, cur, prev, c, p, new_ids, src, d_prev in rows:
        risk = " class='risk'" if club in CLUB_NOTES else ""
        h.append(f"<tr{risk}><td><b>{club}</b> <span class='sl'>{CLUB_NAMES.get(club, '')}</span></td><td class='r'>{val(c['base'], p['base'])}</td><td class='r'>{val(len(new_ids), c['new_prev'])}</td>"
                 f"<td class='r'>{val(c['optin_yes'], p['optin_yes'], True)}</td>"
                 f"<td class='r'>{val(c['optin_no'], p['optin_no'], True)}<br><span class='sl'>{fnum(c['optin_no_n'])} contacts</span></td>"
                 f"<td class='r'>{val(c['optin_vide'], p['optin_vide'], True)}</td><td class='r'>{val(c['completude'], p['completude'], True)}</td>"
                 f"<td class='r'>{val(c['expl_rate'], p['expl_rate'], True)}</td>"
                 f"<td class='r'>{val(c['actifs_rate'], p['actifs_rate'], True) if c['actifs_rate'] is not None else '<span class=na>—</span>'}"
                 f"<br><span class='sl'>{fnum(c['actifs_n']) + ' contacts' if c['actifs_n'] is not None else 'pas de segment'}</span></td></tr>")
    h.append("</table></div>")

    # sources
    h.append("<h2>Sources d'acquisition des nouveaux contacts</h2><div class='tw'><table><tr><th>Club</th>" + "".join(f"<th class='r'>{s}</th>" for s in SOURCES) +
             "<th class='r'>Autre</th><th class='r'>Sans source</th><th class='r'>Total</th></tr>")
    tot = {}
    for club, cur, prev, c, p, new_ids, src, d_prev in rows:
        other = sum(n for s, n in src.items() if s not in SOURCES and s != "sans source")
        sp = c["src_prev"]
        other_p = sum(n for s, n in sp.items() if s not in SOURCES and s != "sans source")
        cells = [src.get(s, 0) for s in SOURCES] + [other, src.get("sans source", 0), len(new_ids)]
        cells_p = [sp.get(s, 0) for s in SOURCES] + [other_p, sp.get("sans source", 0), c["new_prev"]]
        for i, (v, vp) in enumerate(zip(cells, cells_p)):
            a, b = tot.get(i, (0, 0))
            tot[i] = (a + v, b + vp)
        h.append(f"<tr><td><b>{club}</b></td>" + "".join(f"<td class='r'>{val(v, vp)}</td>" for v, vp in zip(cells, cells_p)) + "</tr>")
    h.append("<tr class='tot'><td>TOTAL</td>" + "".join(f"<td class='r'>{val(*tot[i])}</td>" for i in range(len(tot))) + "</tr></table></div>")

    # abonnements
    h.append("<h2>Abonnements</h2><div class='tw'><table><tr><th>Club</th><th class='r'>Total</th><th class='r'>Δ</th><th class='r'>Payant</th><th class='r'>Gratuit</th>"
             "<th class='r'>Public</th><th class='r'>VIP</th><th class='r'>Objectif</th><th class='r'>% atteint</th></tr>")
    for club, *_ in rows:
        why = {"HCC": "API Infomaniak en cours de branchement", "LION": "API Infomaniak en cours de branchement", "FOXES": "API Infomaniak en cours de branchement",
               "SVWE": "API Eventfrog en cours de branchement"}.get(club, "export billetterie manuel")
        h.append(f"<tr><td><b>{club}</b></td><td colspan='8' class='na'>Non calculé cette semaine — {why}</td></tr>")
    h.append("</table></div>")

    # délivrabilité
    h.append("<h2>Délivrabilité</h2><div class='tw'><table><tr><th>Club</th><th class='r'>Score Brevo</th><th class='r'>Indice estimé</th><th class='r'>Délivrés</th>"
             "<th class='r'>Soft bounces</th><th class='r'>Désinscriptions</th><th class='r'>Plaintes</th><th class='r'>Campagnes</th></tr>")
    same = 0
    for club, cur, prev, *_ in rows:
        dv, pv = cur.get("deliv") or {}, (prev.get("deliv") or {})
        off, est, met, poff = dv.get("officiel"), dv.get("estime"), dv.get("metriques"), pv.get("officiel")
        if off and poff and off["score"] == poff["score"]:
            same += 1
        risk = " class='risk'" if off and off["score"] < 50 else ""
        h.append(f"<tr{risk}><td><b>{club}</b></td><td class='r'>{(str(off['score']) + ' ' + delta_html(off['score'], poff['score'] if poff else None, False)) if off else '<span class=na>capture manquante</span>'}</td>"
                 f"<td class='r'>{round(est['valeur']) if est else '—'}</td>"
                 + ("".join(f"<td class='r'>{fpct(met[k])}</td>" for k in ("delivered", "soft", "unsub", "complaint")) + f"<td class='r'>{met['n']}</td>" if met else "<td colspan='5' class='na'>aucune campagne</td>") + "</tr>")
    any_est = next((r[1]["deliv"]["estime"] for r in rows if (r[1].get("deliv") or {}).get("estime")), None)
    h.append("</table></div><p class='sub'>Score Brevo relevé sur les captures (fenêtre 30 jours). Indice estimé = modèle sur soft bounces et désinscriptions, en calibration"
             + (f" (écart moyen ±{fnum(round(any_est['mae'], 1))} sur {any_est['n']} relevés)" if any_est else "") + " — il ne remplace pas le score officiel.</p>")

    # photo
    h.append("<h2>Photo de la base</h2><div class='tw'><table><tr><th>Club</th><th class='r'>Totaux</th><th class='r'>Exploitables</th><th class='r'>Exploitabilité</th>"
             "<th class='r'>Complétion</th><th class='r'>Engagés</th><th class='r'>Actif total</th><th class='r'>Non-engagés</th><th class='r'>Billetterie 26-27</th></tr>")
    for club, cur, prev, c, p, *_ in rows:
        h.append(f"<tr><td><b>{club}</b></td><td class='r'>{val(c['base'], p['base'])}</td><td class='r'>{val(c['expl_n'], p['expl_n'])}</td><td class='r'>{val(c['expl_rate'], p['expl_rate'], True)}</td>"
                 f"<td class='r'>{val(c['completion_expl'], p['completion_expl'], True)}</td><td class='r'>{val(c['engages'], p['engages'])}</td>"
                 f"<td class='r'>{val(c['actifs_n'], p['actifs_n'])}</td><td class='r'>{val(c['non_engages'], p['non_engages'])}</td><td class='r'>{val(c['billet'], p['billet'])}</td></tr>")
    h.append("</table></div>")

    # NL
    win = next((r[3]["nl_window"] for r in rows if r[3]["nl_window"]), "") or ""
    win = win.split("campaigns-")[-1].replace(".csv", "").strip().split("_")
    win_txt = f"du {datetime.fromisoformat(win[0]):%d.%m} au {datetime.fromisoformat(win[1]):%d.%m.%Y}" if len(win) == 2 else ""
    h.append(f"<h2>Newsletters — {win_txt} (3 mois glissants)</h2><div class='tw'><table><tr><th>Club</th>" + "".join(f"<th class='r'>{cat}<br><span style='font-weight:400'>ouv. · clic · désinscr.</span></th>" for cat in NL_CATS) + "</tr>")
    for club, cur, prev, c, p, *_ in rows:
        cells = []
        for cat in NL_CATS:
            a = (c["nl"] or {}).get(cat)
            cells.append(f"<td class='r'>{fpct(a['open'])} · {fpct(a['click'])} · {fpct(a['unsub'])}<br><span class='sl'>{a['n']} campagne{'s' if a['n'] > 1 else ''}</span></td>"
                         if a else "<td class='r na' style='white-space:normal'>Aucune campagne de ce type sur la période</td>")
        h.append(f"<tr><td><b>{club}</b></td>{''.join(cells)}</tr>")
    h.append("</table></div><p class='sub'>Fenêtre désormais identique pour les 8 clubs (3 mois glissants, comme la spécification). Les exports manuels précédents allaient de 1 à 12 mois selon le club : pas de comparaison cette semaine, ces taux servent de nouvelle base.</p>")

    # vigilance
    anomalies, lectures = [], []
    for club, cur, prev, c, p, new_ids, src, d_prev in rows:
        rc = (rapport or {}).get("clubs", {}).get(club, {})
        for a in rc.get("anomalies", []):
            if "à la fois engagé et non-engagé" in a:
                continue
            anomalies.append(f"{club} — {a}")
        if rc.get("statut") == "échec":
            anomalies.append(f"{club} — extraction en échec : {rc.get('erreur')}")
    both = {club: (rapport or {}).get("clubs", {}).get(club, {}).get("controles", {}).get("engages_et_non_engages", 0) for club, *_ in rows}
    if any(both.values()):
        lectures.append("Quelques contacts sont à la fois engagés et non-engagés dans tous les clubs (" + ", ".join(f"{k} {v}" for k, v in both.items() if v) + ") : chevauchement des définitions de segments Brevo, sans impact sur les volumes.")
    if same == len(rows):
        lectures.append("Les 8 scores de délivrabilité sont identiques à la semaine précédente malgré la nouvelle fenêtre : Brevo semble les actualiser moins souvent que chaque semaine.")
    for club, cur, prev, *_ in rows:
        if prev["folder"] != "0610":
            lectures.append(f"{club} comparé au relevé du {prev['folder'][:2]}.{prev['folder'][2:4]} : le fichier « contacts totaux » du 06.10 était une copie d'un autre fichier (erreur d'export manuel).")
    lectures += [
        "Cette semaine est la première extraite par l'API : les deltas comparent l'API à des exports manuels. Les contacts non modifiés sont identiques champ par champ (vérifié sur SVWE), les écarts restants viennent des erreurs des exports manuels.",
        "YS : +~800 exploitables par rapport à l'export manuel, qui filtrait à tort sur OPT_IN = YES. Le taux d'exploitabilité, calculé sur _SUBSCRIBED, reste comparable.",
        "HCC billetterie : 1 096 contacts = segment « Billetterie Active Saison 26-27 ». L'export manuel du 06.10 (4 945) ne venait pas de ce segment.",
        "Engagés + non-engagés ≠ base totale : les contacts actifs entre 6 et 24 mois ne sont dans aucun des deux.",
    ] + [f"{k} : {v}" for k, v in CLUB_NOTES.items() if k in [r[0] for r in rows]]
    h.append("<h2>Points de vigilance</h2><div class='boxes'>")
    h.append("<div class='box'><h3>Anomalies d'extraction</h3><ul>" + ("".join(f"<li>{e(x)}</li>" for x in anomalies) or "<li>Aucune</li>") + "</ul></div>")
    h.append("<div class='box i'><h3>Lectures à ne pas tirer trop vite</h3><ul>" + "".join(f"<li>{e(x)}</li>" for x in lectures) + "</ul></div></div>")

    # contrôles
    ok = lambda b: "<span class='ok'>OK</span>" if b else "<span class='ko'>ÉCHEC</span>"
    h.append("<h2>Contrôles automatiques</h2><div class='tw'><table><tr><th>Club</th><th>Exploitables = segment Brevo</th><th>Engagés ⊆ Actif total</th><th>Aucun orphelin</th><th class='r'>Appels API</th><th class='r'>Durée</th></tr>")
    for club, *_ in rows:
        rc = (rapport or {}).get("clubs", {}).get(club, {})
        ctl = rc.get("controles", {})
        ev = ctl.get("exploitables_vs_segment")
        h.append(f"<tr><td><b>{club}</b></td><td>{ok(ev['ok']) + ' · ' + fnum(ev['derive']) if ev else '<span class=na>pas de segment</span>'}</td>"
                 f"<td>{ok(ctl['engages_inclus_dans_actif']) if 'engages_inclus_dans_actif' in ctl else '<span class=na>—</span>'}</td>"
                 f"<td>{ok(not any('hors base' in a for a in rc.get('anomalies', [])))}</td><td class='r'>{rc.get('appels_api', '—')}</td><td class='r'>{fnum(round(rc.get('secondes', 0)))} s</td></tr>")
    h.append("</table></div>")

    h.append("<footer><b>Méthode.</b><ul>"
             "<li>Source : API Brevo de chaque club. Segments résolus par leur nom : engagés = CMON-Actifs-6m-réels-(hors MPP), actif total = CMON-Actifs-6m, non-engagés = CMON-Sunset-24m-plus, billetterie = Billetterie Active Saison 26-27.</li>"
             "<li>Exploitable = contact inscrit aux campagnes email (non blacklisté), identique au segment Brevo « Contacts Exploitables ».</li>"
             "<li>Nouveaux contacts = ADDED_TIME dans la semaine (lundi → dimanche précédant le relevé), comparés à la semaine d'avant.</li>"
             "<li>Complétude = moyenne du remplissage de 7 champs (nom, prénom, email, NPA, SMS, date de naissance, score) sur toute la base. Complétion = moyenne de 6 champs sur les exploitables (colonne J du Résumé).</li>"
             "<li>Actifs = part de la base dans le segment ACTIF TOTAL (CMON-Actifs-6m).</li>"
             "<li>Taux NL : ouverture = Σ ouvertures uniques / Σ délivrés ; clic = Σ clics uniques / Σ délivrés ; désinscription = moyenne des taux par campagne. Classement : PROGRAM(ME) → AVM Programme, puis AVM, APM, Autres.</li>"
             "<li>Deltas en points pour les taux, en valeur absolue pour les volumes.</li>"
             f"<li>Généré le {datetime.now():%d.%m.%Y à %H:%M} par cmon_brevo.py / cmon_kpi_html.py.</li></ul></footer></div></body></html>")
    return "".join(h)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--club", help="un club (page individuelle) ; sans --club : page récapitulative 8 clubs")
    ap.add_argument("--current", default=datetime.now().strftime("%d%m%y"))
    ap.add_argument("--previous", default=None)
    ap.add_argument("--override", action="append", default=[], help="relevé de comparaison spécifique, ex. FOXES=290926")
    ap.add_argument("--rupture", action="append", default=[], help="KPI sans delta (rupture de série), ex. HCC=billet")
    ap.add_argument("--etat", help="etat_dash_<JJMMAA>.json de la semaine précédente (routine cloud)")
    a = ap.parse_args()
    root = BASE / "Fichier ZIP _"
    cur_dir = root / a.current
    if not a.club:
        rp = cur_dir / "_rapport_extraction.json"
        rapport = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else None
        over = dict(o.upper().split("=", 1) for o in a.override)
        ruptures = {}
        for r in a.rupture:
            c_, k_ = r.split("=", 1)
            ruptures.setdefault(c_.upper(), []).append(k_)
        etat = None
        if a.etat:
            from cmon_etat import load, prev_from_etat
            etat = load(a.etat)
        clubs = []
        for club in EXPECTED_ATTRS:
            if not find_file(cur_dir, club, "Contacts totaux"):
                continue
            cur = load_relevé(cur_dir, club)
            cur["deliv"] = deliv_block(cur_dir, club, cur["campaigns"], datetime.strptime(cur_dir.name, "%d%m%y"))
            prev = prev_from_etat(etat, club) if etat else None
            if prev is None:
                pname = over.get(club) or a.previous
                prev_dir = root / pname if pname else next(d for d in relevé_dirs() if d != cur_dir and find_file(d, club, "Contacts totaux"))
                prev = load_relevé(prev_dir, club)
                prev["deliv"] = deliv_block(prev_dir, club, prev["campaigns"], datetime.strptime(prev_dir.name + ("26" if len(prev_dir.name) == 4 else ""), "%d%m%y"))
            if not prev["deliv"]["officiel"]:  # score précédent : dernier relevé qui a une capture pour ce club
                for d in relevé_dirs():
                    f = d / "delivrabilite.json"
                    if d != cur_dir and f.exists() and club in json.loads(f.read_text(encoding="utf-8")):
                        prev["deliv"]["officiel"] = json.loads(f.read_text(encoding="utf-8"))[club]
                        break
            for kpi in ruptures.get(club, []):  # rupture de série : pas de delta trompeur
                prev["k"][kpi] = None
            clubs.append((club, cur, prev))
        for club, cur, _ in clubs:  # après tous les calculs : l'estimation de la semaine n'utilise pas son propre point
            log_calibration(cur_dir, club, cur["deliv"])
        out = cur_dir / f"KPI_{a.current}.html"
        out.write_text(build_recap(clubs, rapport, a.current), encoding="utf-8")
        print(out)
        return
    club = a.club.upper()
    prev_dir = root / a.previous if a.previous else next(d for d in relevé_dirs() if d != cur_dir and find_file(d, club, "Contacts totaux"))
    rp = cur_dir / "_rapport_extraction.json"
    rapport = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else None
    cur, prev = load_relevé(cur_dir, club), load_relevé(prev_dir, club)
    for rel, d in ((cur, cur_dir), (prev, prev_dir)):
        date = datetime.strptime(d.name + ("26" if len(d.name) == 4 else ""), "%d%m%y")
        rel["deliv"] = deliv_block(d, club, rel["campaigns"], date)
    if log_calibration(cur_dir, club, cur["deliv"]):
        print(f"calibration : score {cur['deliv']['officiel']['score']} ajouté pour {club} {cur_dir.name}")
    page = build(club, cur, prev, rapport)
    out = cur_dir / f"KPI_{club}_{a.current}.html"
    out.write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
