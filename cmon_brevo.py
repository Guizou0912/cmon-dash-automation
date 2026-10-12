#!/usr/bin/env python3
"""C'mon Sports — extraction Brevo pour le Dash Performance.

Phase 1 : mode --discover (lecture seule, aucun fichier de production écrit).

    python cmon_brevo.py --discover --club SVWE [--test-export]

Lit les clés dans brevo_keys.json (même dossier). Aucune valeur de clé n'est
jamais affichée, loggée ou écrite.
"""
import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
KEYS_FILE = BASE / "brevo_keys.json"
REF_DIR = BASE / "Fichier ZIP _" / "290926"
API = "https://api.brevo.com/v3"

# §6.2 — attributs attendus par club (None = absent attendu)
EXPECTED_ATTRS = {
    "CHAM":  {"NPA": "AX_ZIP_CODE", "ANNIVERSAIRE": "AX_BIRTHDATE", "CMON_SCORE": "CMON_SCORE", "CMON_SCORE_26_27": "CMON_SCORE_26_27"},
    "FOB":   {"NPA": "AX_ZIP_CODE", "ANNIVERSAIRE": "ANNIVERSAIRE", "CMON_SCORE": "CMON_SCORE", "CMON_SCORE_26_27": "CMON_SCORE_26_27"},
    "FOXES": {"NPA": "NPA", "ANNIVERSAIRE": "DATE_ANNIVERSAIRE", "CMON_SCORE": "CMON_SCORE", "CMON_SCORE_26_27": "CMON_SCORE_26_27"},
    "HCC":   {"NPA": "NPA", "ANNIVERSAIRE": "ANNIVERSAIRE", "CMON_SCORE": "SCORE", "CMON_SCORE_26_27": "CMON_SCORE_26_27"},
    "LION":  {"NPA": "NPA", "ANNIVERSAIRE": "ANNIVERSAIRE", "CMON_SCORE": "CMON_SCORE", "CMON_SCORE_26_27": "CMON_SCORE_26_27"},
    "LS":    {"NPA": "AX_ZIP_CODE", "ANNIVERSAIRE": "AX_BIRTHDATE", "CMON_SCORE": "CMON_SCORE", "CMON_SCORE_26_27": None},
    "SVWE":  {"NPA": "NPA", "ANNIVERSAIRE": "AX_BIRTHDAY", "CMON_SCORE": "CMON_SCORE", "CMON_SCORE_26_27": "CMON_SCORE_26_27"},
    "YS":    {"NPA": "AX_ZIP_CODE", "ANNIVERSAIRE": "AX_BIRTHDATE", "CMON_SCORE": "CMON_SCORE", "CMON_SCORE_26_27": "CMON_SCORING_26_27"},
}
COMMON_ATTRS = ["NOM", "PRENOM", "SMS", "OPT_IN"]

# §6.1 — exports cibles et mots-clés de rapprochement (normalisés, sans accents)
EXPORTS = {
    "Contacts totaux":                  {"file": "{c} Contacts totaux.csv",                  "kw": [["total"], ["totaux"], ["tous"]]},
    "Contacts exploitables":            {"file": "{c} Contacts exploitables .csv",           "kw": [["exploitable"]]},
    "Contacts engagés":                 {"file": "{c} Contacts engagés.csv",                 "kw": [["engage"]], "not": ["non"]},
    "Contacts non-engagés":             {"file": "{c} Contacts non-engagés.csv",             "kw": [["non", "engage"]]},
    "Billetterie Active Saison 26-27":  {"file": "{c} Billetterie Active Saison 26-27.csv",  "kw": [["billetterie"], ["billet"]]},
    "ACTIF TOTAL":                      {"file": "{c} ACTIF TOTAL.csv",                      "kw": [["actif"]]},
}


class BrevoError(Exception):
    pass


class Brevo:
    def __init__(self, club, key):
        self.club = club
        self._key = key
        self.calls = 0

    def req(self, method, path, params=None, body=None, retries=6):
        url = API + path
        if params:
            url += "?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items() if v is not None)
        data = json.dumps(body).encode() if body is not None else None
        delay = 2
        for attempt in range(retries):
            r = urllib.request.Request(url, data=data, method=method, headers={
                "api-key": self._key, "accept": "application/json", "content-type": "application/json"})
            self.calls += 1
            try:
                with urllib.request.urlopen(r, timeout=60) as resp:
                    raw = resp.read()
                    return resp.status, (json.loads(raw) if raw else {})
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < retries - 1:
                    reset = e.headers.get("x-sib-ratelimit-reset")
                    time.sleep(max(delay, int(reset) if reset and reset.isdigit() else 0))
                    delay *= 2
                    continue
                if e.code == 401:
                    raise BrevoError(f"clé invalide pour {self.club}") from None
                deny = e.headers.get("x-deny-reason")
                try:
                    msg = json.loads(e.read() or b"{}").get("message", "")
                except Exception:
                    msg = ""
                raise BrevoError(f"{method} {path} -> HTTP {e.code}" + (f" [x-deny-reason: {deny}]" if deny else "") + (f" : {msg}" if msg else "")) from None
            except urllib.error.URLError as e:
                if attempt < retries - 1:
                    time.sleep(delay); delay *= 2
                    continue
                raise BrevoError(f"{method} {path} -> erreur réseau : {e.reason}") from None
        raise BrevoError(f"{method} {path} -> 429 persistant après {retries} tentatives")

    def get(self, path, **params):
        return self.req("GET", path, params)[1]

    def paged(self, path, key, limit=50):
        out, offset = [], 0
        while True:
            page = self.get(path, limit=limit, offset=offset)
            items = page.get(key) or []
            out += items
            offset += len(items)
            if not items or offset >= page.get("count", 0):
                return out


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", s)


def load_keys():
    """brevo_keys.json en local ; dans la routine cloud, variables d'environnement BREVO_KEY_<CLUB>."""
    import os
    env = {k[len("BREVO_KEY_"):].upper(): v for k, v in os.environ.items() if k.startswith("BREVO_KEY_") and v.strip()}
    if env:
        return env
    if not KEYS_FILE.exists():
        sys.exit(f"Aucune clé : ni variables BREVO_KEY_<CLUB>, ni {KEYS_FILE}\n"
                 "Crée le fichier avec au minimum {\"SVWE\": \"xkeysib-...\"} (ne jamais le committer).")
    keys = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
    return {k.upper(): v for k, v in keys.items() if isinstance(v, str) and v.strip() and "..." not in v}


def ref_counts(club):
    """Nombre de lignes et IDs des CSV du relevé de référence pour ce club."""
    out = {}
    if not REF_DIR.exists():
        return out
    for f in REF_DIR.glob("*.csv"):
        if not f.name.upper().startswith(club + " "):
            continue
        with f.open(encoding="utf-8-sig", newline="") as fh:
            ids = {r.get("CONTACT ID") for r in csv.DictReader(fh, delimiter=";")}
        out[f.name] = {"rows": len(ids), "ids": ids}
    return out


def propose_mapping(lists, segments, refs, seg_counts):
    rows = []
    for export, spec in EXPORTS.items():
        cands = []
        for kind, items in (("segment", segments), ("liste", lists)):
            for it in items:
                tokens = norm(it["name"])
                joined = " ".join(tokens)
                hit = any(all(any(t.startswith(w) for t in tokens) for w in grp) for grp in spec["kw"])
                if hit and any(n in tokens for n in spec.get("not", [])):
                    hit = False
                if hit:
                    cnt = seg_counts.get(it["id"]) if kind == "segment" else it.get("uniqueSubscribers", it.get("totalSubscribers"))
                    cands.append({"type": kind, "id": it["id"], "name": it["name"], "count": cnt, "_j": joined})
        ref_file = next((n for n in refs if norm(n)[1:] == norm(spec["file"].format(c="X"))[1:]), None)
        ref_rows = refs[ref_file]["rows"] if ref_file else None
        if not cands:
            conf, why = "aucune", "aucun nom de liste/segment ne correspond"
            choice = None
        else:
            # préfère le candidat dont le volume est le plus proche de la référence
            if ref_rows is not None and any(c["count"] is not None for c in cands):
                cands.sort(key=lambda c: abs((c["count"] or 0) - ref_rows))
            choice = cands[0]
            delta = None if ref_rows is None or choice["count"] is None else choice["count"] - ref_rows
            if len(cands) == 1 and delta is not None and abs(delta) <= max(30, ref_rows * 0.02):
                conf = "haute"
            elif delta is not None and abs(delta) <= max(30, ref_rows * 0.02):
                conf = "moyenne"
            else:
                conf = "basse"
            why = f"{len(cands)} candidat(s) ; volume API {choice['count']} vs réf 290926 {ref_rows}" + (f" (Δ {delta:+d})" if delta is not None else "")
        rows.append({"export": export, "fichier": spec["file"], "choix": {k: v for k, v in (choice or {}).items() if k != "_j"} or None,
                     "autres_candidats": [{k: v for k, v in c.items() if k != "_j"} for c in cands[1:]],
                     "ref_290926": ref_rows, "confiance": conf, "justification": why})
    return rows


def test_export(api, segment_id, attrs, timeout=600):
    """Piste 1 : POST /contacts/export avec customContactFilter.segmentId, poll du process."""
    body = {"exportAttributes": attrs, "customContactFilter": {"actionForContacts": "allContacts", "segmentId": segment_id}}
    t0 = time.time()
    status, resp = api.req("POST", "/contacts/export", body=body)
    pid = resp.get("processId")
    if not pid:
        return {"ok": False, "detail": f"pas de processId (HTTP {status})", "response": resp}
    while time.time() - t0 < timeout:
        p = api.get(f"/processes/{pid}")
        st = p.get("status")
        if st == "completed":
            url = p.get("export_url") or p.get("exportUrl")
            rows = None
            if url:
                # storage.brevo.com renvoie 403 sans User-Agent navigateur
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120) as r:
                    text = r.read().decode("utf-8-sig")
                rows = max(0, len([l for l in text.splitlines() if l.strip()]) - 1)
                header = text.splitlines()[0] if text else ""
            return {"ok": True, "processId": pid, "secondes": round(time.time() - t0), "lignes": rows,
                    "entete": header[:300] if url else None}
        if st in ("failed", "aborted"):
            return {"ok": False, "processId": pid, "detail": f"process {st}"}
        time.sleep(5)
    return {"ok": False, "processId": pid, "detail": f"process non terminé après {timeout}s"}


def discover(club, key, do_export):
    api = Brevo(club, key)
    rep = {"club": club, "date": datetime.now().isoformat(timespec="seconds"), "anomalies": []}

    acc = api.get("/account")
    rep["compte"] = {"email": acc.get("email"), "societe": acc.get("companyName"),
                     "plans": [p.get("name") or p.get("type") for p in acc.get("planVerticals") or acc.get("plan") or []],
                     "enterprise": acc.get("enterprise")}

    attrs = api.get("/contacts/attributes").get("attributes", [])
    rep["attributs"] = [{"nom": a["name"], "categorie": a.get("category"), "type": a.get("type")} for a in attrs]
    names = {a["name"] for a in attrs}
    ecarts = []
    for role, expected in EXPECTED_ATTRS.get(club, {}).items():
        if expected is None:
            if any(n.upper().endswith("26_27") and "SCOR" in n.upper() for n in names):
                ecarts.append(f"{role} : attendu absent, mais trouvé {[n for n in names if 'SCOR' in n.upper() and '26_27' in n]}")
        elif expected not in names:
            similar = [n for n in names if any(t in n.upper() for t in norm(expected)[0].upper().split("_")[:1])]
            ecarts.append(f"{role} : attendu `{expected}` ABSENT de l'API" + (f" (proches : {similar[:5]})" if similar else ""))
    for c in COMMON_ATTRS:
        if c not in names:
            ecarts.append(f"attribut commun `{c}` absent")
    rep["ecarts_attributs_6_2"] = ecarts or ["aucun écart"]

    lists = api.paged("/contacts/lists", "lists")
    segments = api.paged("/contacts/segments", "segments")
    rep["listes"] = [{"id": l["id"], "nom": l["name"], "abonnes": l.get("uniqueSubscribers", l.get("totalSubscribers")),
                      "dossier": l.get("folderId")} for l in lists]

    # Piste 2 : GET /contacts?segmentId=… — `count` donne le volume du segment en 1 appel
    seg_counts, seg_errors = {}, {}
    for s in segments:
        try:
            seg_counts[s["id"]] = api.get("/contacts", segmentId=s["id"], limit=1).get("count")
        except BrevoError as e:
            seg_errors[s["id"]] = str(e)
    rep["segments"] = [{"id": s["id"], "nom": s.get("segmentName") or s.get("name"), "categorie": s.get("categoryName"),
                        "maj": s.get("updatedAt"), "volume_api": seg_counts.get(s["id"]), "erreur": seg_errors.get(s["id"])}
                       for s in segments]
    for s in segments:
        s.setdefault("name", s.get("segmentName", ""))

    total = api.get("/contacts", limit=1).get("count")
    refs = ref_counts(club)
    rep["base_totale_api"] = total
    rep["reference_290926"] = {n: v["rows"] for n, v in refs.items()}
    rep["mapping_propose"] = propose_mapping(lists, segments, refs, seg_counts)

    # Contrôle par IDs : un segment lu via GET /contacts doit recouper la référence
    verdict = {"get_contacts_segmentId": "ok" if seg_counts and not seg_errors else ("partiel" if seg_counts else "échec")}
    small = min((m for m in rep["mapping_propose"] if m["choix"] and m["choix"]["type"] == "segment" and m["choix"]["count"]),
                key=lambda m: m["choix"]["count"], default=None)
    if small:
        sid = small["choix"]["id"]
        ids, offset = set(), 0
        while True:
            page = api.get("/contacts", segmentId=sid, limit=1000, offset=offset)
            batch = page.get("contacts") or []
            ids |= {str(c["id"]) for c in batch}
            offset += len(batch)
            if not batch or offset >= page.get("count", 0):
                break
        ref_name = next((n for n in refs if norm(n)[1:] == norm(small["fichier"].format(c="X"))[1:]), None)
        ref_ids = refs[ref_name]["ids"] if ref_name else set()
        verdict["controle_ids"] = {"segment": small["choix"]["name"], "id": sid, "ids_api": len(ids),
                                   "ids_ref_290926": len(ref_ids), "communs": len(ids & ref_ids),
                                   "api_seulement": len(ids - ref_ids), "ref_seulement": len(ref_ids - ids)}
        if do_export:
            wanted = [a for a in ("EMAIL", "OPT_IN", "CMON_SCORE", "NPA") if a in names]
            try:
                verdict["post_contacts_export"] = test_export(api, sid, wanted)
            except BrevoError as e:
                verdict["post_contacts_export"] = {"ok": False, "detail": str(e)}
    rep["verdict_segments"] = verdict

    # anomalie connue §7 : exploitables == totaux
    ex = next((m for m in rep["mapping_propose"] if m["export"] == "Contacts exploitables"), None)
    if ex and ex["choix"] and ex["choix"]["count"] == total:
        rep["anomalies"].append("Le segment « exploitables » a le même volume que la base totale (anomalie §7 SVWE).")
    rep["appels_api"] = api.calls
    return rep


# ---------------------------------------------------------------- phase 2 : extraction

# §6.1 bis — fichier de sortie <- nom du segment Brevo (résolu en ID à chaque exécution)
SEGMENTS = {
    "Contacts engagés":                "CMON-Actifs-6m-réels-(hors MPP)",
    "Contacts non-engagés":            "CMON-Sunset-24m-plus",
    "ACTIF TOTAL":                     "CMON-Actifs-6m",
    "Billetterie Active Saison 26-27": "Billetterie Active Saison 26-27",
}
EXPLOITABLES_CONTROL = "Contacts Exploitables"
OUT_NAMES = {
    "Contacts totaux": "{c} Contacts totaux.csv",
    "Contacts exploitables": "{c} Contacts exploitables .csv",
    "Contacts engagés": "{c} Contacts engagés.csv",
    "Contacts non-engagés": "{c} Contacts non-engagés.csv",
    "Billetterie Active Saison 26-27": "{c} Billetterie Active Saison 26-27.csv",
    "ACTIF TOTAL": "{c} ACTIF TOTAL.csv",
}
CAMPAIGN_COLS = ["Campaign ID", "Campaign Name", "Name from", "Email from", "Sending date", "Subject", "Sent",
                 "Non delivered", "Hard bounces", "Soft bounces", "Non delivered rate", "Delivered", "Total opens",
                 "Opens", "Trackable open rate", "Apple MPP Opens", "Total clicked", "Clicked", "Click rate",
                 "Click-to-Open rate", "Unsubscribed", "Unsubscription rate", "Delivered rate", "Hard Bounces rate",
                 "Soft Bounces rate", "Complaints", "Complaints rate"]


def relevé_dirs():
    """Dossiers de relevés existants, du plus récent au plus ancien (noms JJMM ou JJMMAA)."""
    root = BASE / "Fichier ZIP _"
    out = []
    for d in root.iterdir() if root.exists() else []:
        if d.is_dir() and re.fullmatch(r"\d{4}(\d{2})?", d.name):
            dd, mm, yy = int(d.name[:2]), int(d.name[2:4]), int(d.name[4:] or 26)
            try:
                out.append((datetime(2000 + yy, mm, dd), d))
            except ValueError:
                pass
    return [d for _, d in sorted(out, reverse=True)]


KIND_TOKENS = {  # lecture tolérante des noms historiques (§6.1)
    "Contacts totaux": [["total"], ["totaux"]],
    "Contacts exploitables": [["exploitable"]],
    "Contacts engagés": [["engage"]],
    "Contacts non-engagés": [["non", "engage"]],
    "Billetterie Active Saison 26-27": [["billetterie"]],
    "ACTIF TOTAL": [["actif"]],
    "campaigns": [["campaigns"]],
}


def find_file(folder, club, kind):
    hits = []
    for f in folder.glob("*.csv"):
        toks = norm(f.stem)
        if not toks or not (toks[0] == club.lower() or club.lower() in toks or toks[0].startswith(club.lower())):
            continue
        if not any(all(any(t.startswith(w) for t in toks) for w in grp) for grp in KIND_TOKENS[kind]):
            continue
        if kind == "Contacts engagés" and "non" in toks:
            continue
        if kind == "Contacts totaux" and any(t.startswith("actif") for t in toks):
            continue
        hits.append(f)
    return sorted(hits, key=lambda p: len(p.name))[0] if hits else None


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        r = csv.DictReader(fh, delimiter=";")
        return r.fieldnames, list(r)


def fmt_date(v):
    if not v:
        return ""
    try:
        return datetime.fromisoformat(str(v)[:10]).strftime("%d-%m-%Y")
    except ValueError:
        return str(v)


def to_row(c, attr_meta):
    a = c.get("attributes") or {}
    row = {"CONTACT ID": str(c["id"]), "EMAIL": c.get("email") or ""}
    for name, meta in attr_meta.items():
        v = a.get(name)
        if v is None or v == "":
            row[name] = ""
        elif meta["type"] == "boolean":
            row[name] = "YES" if v is True else "NO"
        elif meta["type"] == "date":
            row[name] = fmt_date(v)
        elif meta.get("enum"):
            row[name] = meta["enum"].get(str(v), str(v))
        elif isinstance(v, float) and v.is_integer():
            row[name] = str(int(v))
        else:
            row[name] = str(v)
    row["ADDED_TIME"] = fmt_date(c.get("createdAt"))
    row["MODIFIED_TIME"] = fmt_date(c.get("modifiedAt"))
    sub = [x for x, blk in (("email_marketing", c.get("emailBlacklisted")), ("sms_marketing", c.get("smsBlacklisted"))) if not blk]
    blk = [x for x, b in (("email_marketing", c.get("emailBlacklisted")), ("sms_marketing", c.get("smsBlacklisted"))) if b]
    row["_SUBSCRIBED"] = "[" + "|".join(f"'{x}'" for x in sub) + "]" if sub else ""
    row["_BLOCKLISTED"] = "[" + "|".join(f"'{x}'" for x in blk) + "]" if blk else ""
    return row


def pull_contacts(api, **filters):
    out, offset = [], 0
    while True:
        page = api.get("/contacts", limit=1000, offset=offset, **filters)
        batch = page.get("contacts") or []
        out += batch
        offset += len(batch)
        if not batch or offset >= page.get("count", 0):
            return out


def pct(n, d):
    return f"{n / d * 100:.2f}%".replace(".", ",") if d else "0,00%"


def extract_campaigns(api, start, end):
    rows, offset = [], 0
    while True:
        page = api.get("/emailCampaigns", status="sent", statistics="globalStats", limit=50, offset=offset,
                       startDate=start.strftime("%Y-%m-%dT00:00:00.000+02:00"),
                       endDate=min(end, datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S.000+02:00"))  # horloge locale parfois en avance sur Brevo
        items = page.get("campaigns") or []
        for c in items:
            s = (c.get("statistics") or {}).get("globalStats") or {}
            sent, dlv = s.get("sent", 0), s.get("delivered", 0)
            hb, sb, op, cl = s.get("hardBounces", 0), s.get("softBounces", 0), s.get("uniqueViews", 0), s.get("uniqueClicks", 0)
            rows.append({
                "Campaign ID": c["id"], "Campaign Name": c.get("name", ""), "Name from": (c.get("sender") or {}).get("name", ""),
                "Email from": (c.get("sender") or {}).get("email", ""),
                "Sending date": (c.get("sentDate") or "")[:19].replace("T", " "), "Subject": c.get("subject", ""),
                "Sent": sent, "Non delivered": hb + sb, "Hard bounces": hb, "Soft bounces": sb,
                "Non delivered rate": pct(hb + sb, sent), "Delivered": dlv, "Total opens": s.get("viewed", 0),
                "Opens": op, "Trackable open rate": pct(op, dlv), "Apple MPP Opens": s.get("appleMppOpens", 0),
                "Total clicked": s.get("clickers", 0), "Clicked": cl, "Click rate": pct(cl, dlv),
                "Click-to-Open rate": pct(cl, op), "Unsubscribed": s.get("unsubscriptions", 0),
                "Unsubscription rate": pct(s.get("unsubscriptions", 0), dlv), "Delivered rate": pct(dlv, sent),
                "Hard Bounces rate": pct(hb, sent), "Soft Bounces rate": pct(sb, sent),
                "Complaints": s.get("complaints", 0), "Complaints rate": pct(s.get("complaints", 0), dlv)})
        offset += len(items)
        if not items or offset >= page.get("count", 0):
            break
    rows.sort(key=lambda r: r["Sending date"], reverse=True)
    return rows


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def extract_club(club, key, outdir, camp_start, camp_end):
    t0 = time.time()
    api = Brevo(club, key)
    rep = {"club": club, "fichiers": {}, "anomalies": [], "controles": {}}

    attrs = api.get("/contacts/attributes").get("attributes", [])
    meta = {}
    for a in attrs:
        if a.get("category") in ("normal", "category"):
            meta[a["name"]] = {"type": a.get("type") or ("category" if a.get("enumeration") else "text"),
                               "enum": {str(e["value"]): e["label"] for e in a.get("enumeration") or []} or None}
    # ordre des colonnes : celui du dernier export manuel du club s'il existe, sinon celui de l'API
    header = None
    for d in relevé_dirs():
        f = find_file(d, club, "Contacts totaux")
        if f:
            header = read_csv(f)[0]
            break
    tail = ["ADDED_TIME", "MODIFIED_TIME", "_SUBSCRIBED", "_BLOCKLISTED"]
    if header:
        header = [h for h in header if h in meta or h in ("CONTACT ID", "EMAIL") or h in tail or h.startswith("sib_")]
        header[-4:-4] = [m for m in meta if m not in header]
        header = [h for h in header if h not in tail] + tail
    else:
        header = ["CONTACT ID", "EMAIL"] + list(meta) + tail

    contacts = pull_contacts(api)
    total = {str(c["id"]): to_row(c, meta) for c in contacts}
    rows_by_file = {"Contacts totaux": list(total.values()),
                    "Contacts exploitables": [r for r in total.values() if "email_marketing" in r["_SUBSCRIBED"]]}

    segs = {(s.get("segmentName") or s.get("name")): s["id"] for s in api.paged("/contacts/segments", "segments")}
    seg_ids = {}
    for out, seg_name in SEGMENTS.items():
        if seg_name not in segs:
            rep["anomalies"].append(f"segment « {seg_name} » introuvable — fichier « {out} » non produit")
            continue
        ids = [str(c["id"]) for c in pull_contacts(api, segmentId=segs[seg_name])]
        seg_ids[out] = set(ids)
        orphans = [i for i in ids if i not in total]
        if orphans:
            rep["anomalies"].append(f"{out} : {len(orphans)} contact(s) hors base totale")
        rows_by_file[out] = [total[i] for i in ids if i in total]

    # contrôles
    if EXPLOITABLES_CONTROL in segs:
        n = api.get("/contacts", segmentId=segs[EXPLOITABLES_CONTROL], limit=1).get("count")
        ok = n == len(rows_by_file["Contacts exploitables"])
        rep["controles"]["exploitables_vs_segment"] = {"derive": len(rows_by_file["Contacts exploitables"]), "segment": n, "ok": ok}
        if not ok:
            rep["anomalies"].append(f"exploitables dérivés ({len(rows_by_file['Contacts exploitables'])}) ≠ segment Brevo ({n})")
    if {"Contacts engagés", "ACTIF TOTAL"} <= set(seg_ids):
        out_ = seg_ids["Contacts engagés"] - seg_ids["ACTIF TOTAL"]
        rep["controles"]["engages_inclus_dans_actif"] = not out_
        if out_:
            rep["anomalies"].append(f"{len(out_)} engagé(s) hors ACTIF TOTAL — segment mal résolu ?")
    if {"Contacts engagés", "Contacts non-engagés"} <= set(seg_ids):
        both = seg_ids["Contacts engagés"] & seg_ids["Contacts non-engagés"]
        rep["controles"]["engages_et_non_engages"] = len(both)
        if both:
            rep["anomalies"].append(f"{len(both)} contact(s) à la fois engagé et non-engagé (IDs {', '.join(sorted(both))}) — recalcul de segment côté Brevo probable")

    for kind, rows in rows_by_file.items():
        name = OUT_NAMES[kind].format(c=club)
        write_csv(outdir / name, header, rows)
        rep["fichiers"][name] = len(rows)

    camps = extract_campaigns(api, camp_start, camp_end)
    cname = f"{club} email-campaigns-{camp_start:%Y-%m-%d}_{camp_end:%Y-%m-%d}.csv"
    write_csv(outdir / cname, CAMPAIGN_COLS, camps)
    rep["fichiers"][cname] = len(camps)

    rep["contact_le_plus_recent"] = max((c.get("createdAt") or "" for c in contacts), default=None)
    rep["appels_api"] = api.calls
    rep["secondes"] = round(time.time() - t0, 1)
    return rep


def extract(clubs, keys, outdir, camp_days):
    outdir.mkdir(parents=True, exist_ok=True)
    end = datetime.now()
    start = datetime.fromordinal(end.toordinal() - camp_days)
    rapport = {"date": end.isoformat(timespec="seconds"), "dossier": str(outdir),
               "fenetre_campagnes": f"{start:%Y-%m-%d} → {end:%Y-%m-%d}", "clubs": {}}
    for club in clubs:
        if club not in keys:
            rapport["clubs"][club] = {"statut": "ignoré", "raison": "absent de brevo_keys.json"}
            continue
        try:
            r = extract_club(club, keys[club], outdir, start, end)
            r["statut"] = "ok" if not r["anomalies"] else "ok avec anomalies"
        except Exception as e:  # un club en échec n'arrête jamais les autres
            r = {"statut": "échec", "erreur": str(e) if isinstance(e, BrevoError) else f"{type(e).__name__}: {e}"}
        rapport["clubs"][club] = r
        print(f"[{club}] {r['statut']}", flush=True)
    (outdir / "_rapport_extraction.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    return rapport


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--club", default=None, help="un seul club (défaut : SVWE en discover, tous en extract)")
    ap.add_argument("--test-export", action="store_true", help="tester aussi POST /contacts/export (asynchrone)")
    ap.add_argument("--campaign-days", type=int, default=91, help="fenêtre newsletters (spec : 3 mois glissants)")
    ap.add_argument("--campaigns-only", action="store_true", help="ne recharger que les exports campagnes")
    a = ap.parse_args()
    keys = load_keys()
    if a.extract:
        clubs = [a.club.upper()] if a.club else list(EXPECTED_ATTRS)
        outdir = BASE / "Fichier ZIP _" / datetime.now().strftime("%d%m%y")
        if a.campaigns_only:
            end = datetime.now()
            start = datetime.fromordinal(end.toordinal() - a.campaign_days)
            for club in clubs:
                if club not in keys:
                    continue
                for old in outdir.glob(f"{club} email-campaigns-*.csv"):
                    old.unlink()
                rows = extract_campaigns(Brevo(club, keys[club]), start, end)
                write_csv(outdir / f"{club} email-campaigns-{start:%Y-%m-%d}_{end:%Y-%m-%d}.csv", CAMPAIGN_COLS, rows)
                print(f"[{club}] {len(rows)} campagnes", flush=True)
            return
        rep = extract(clubs, keys, outdir, a.campaign_days)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return
    if not a.discover:
        ap.error("choisir --discover ou --extract")
    club = (a.club or "SVWE").upper()
    if club not in keys:
        sys.exit(f"{club} absent de brevo_keys.json — rien à faire.")
    try:
        rep = discover(club, keys[club], a.test_export)
    except BrevoError as e:
        sys.exit(f"[{club}] {e}")
    out = BASE / f"_discover_{club}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print(f"\nRapport écrit : {out}")


if __name__ == "__main__":
    main()
