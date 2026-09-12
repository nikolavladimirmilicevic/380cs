#!/usr/bin/env python3
"""
38-0 rating engine.

Turns real player-season statistics into an editorial-style 0-99 rating,
position-aware, plus a "prime" rating (a player's best season in the data).

Data model per output row:
    {player, club, season, position, seasonRating, primeRating}

Sources
-------
- FPL-format season CSVs (goals, assists, minutes, clean sheets, saves, ICT,
  bps, etc.). Works on the live FPL API for the current season and on the
  vaastav/Fantasy-Premier-League archive for 2016-17 onward.
- FBref history (1992-2016) is added by fbref_history.py in CI, emitting the
  same intermediate rows; both feed rate_all().

The model is intentionally transparent (a weighted, position-specific blend of
per-90 output, reliability-shrunk for small samples, plus a playing-time term),
percentile-mapped within each season and position. Tune the weights below; that
is where "your" rating philosophy lives.
"""

import csv, io, json, math, os, sys, urllib.request

ARCHIVE = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"
SEASONS = ["2016-17","2017-18","2018-19","2019-20","2020-21",
           "2021-22","2022-23","2023-24","2024-25","2025-26","2026-27"]
POS = {1:"GK", 2:"DEF", 3:"MID", 4:"FWD"}

# ---- reliability & mapping knobs -------------------------------------------
REL_K   = 6.0     # per-90 shrinkage: 90*K minutes ~ half trust
VOL_W   = 0.35    # weight of playing-time relative to per-90 performance
RAT_LO  = 47.0    # rating floor
RAT_HI  = 97.0    # rating ceiling
GAMMA   = 1.15    # >1 thins out the top of the distribution

def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

# season -> {team_id -> club name}. Primary: master list; fallback: teams.csv
_MASTER = None
def master_map():
    global _MASTER
    if _MASTER is None:
        _MASTER = {}
        rdr = csv.DictReader(io.StringIO(fetch(f"{ARCHIVE}/master_team_list.csv")))
        for r in rdr:
            _MASTER.setdefault(r["season"], {})[r["team"]] = r["team_name"]
    return _MASTER

def team_names(season):
    m = master_map().get(season)
    if m:
        return m
    teams = list(csv.DictReader(io.StringIO(fetch(f"{ARCHIVE}/{season}/teams.csv"))))
    return {t["id"]: t["name"] for t in teams}

# ---- build intermediate rows from FPL-shaped records -----------------------
# Both the CSV archive and the live bootstrap-static API use the same field
# names (goals_scored, assists, minutes, clean_sheets, saves, bps, influence,
# creativity, threat, goals_conceded, element_type, team, code, web_name), so
# one row builder serves both.
def rows_from_elements(elements, id2name, season):
    rows = []
    for p in elements:
        minutes = num(p.get("minutes"))
        if minutes < 1:
            continue
        n90 = minutes / 90.0
        rel = n90 / (n90 + REL_K)          # small-sample shrink for rate stats
        def per90(k): return (num(p.get(k)) / n90) * rel if n90 > 0 else 0.0
        rows.append({
            "code": str(p.get("code") or p.get("id")),
            "player": p.get("web_name") or (str(p.get("first_name") or "")+" "+str(p.get("second_name") or "")).strip(),
            "club": id2name.get(str(p.get("team")), p.get("team")),
            "season": season,
            "pos": POS.get(int(num(p.get("element_type")) or 3), "MID"),
            "minutes": minutes,
            "g90": per90("goals_scored"),
            "a90": per90("assists"),
            "thr90": per90("threat"),
            "cre90": per90("creativity"),
            "inf90": per90("influence"),
            "bps90": per90("bps"),
            "sav90": per90("saves"),
            "cs_rate": (num(p.get("clean_sheets")) / n90) * rel if n90 > 0 else 0.0,
            "gc90": per90("goals_conceded"),
            "psv": num(p.get("penalties_saved")),
        })
    return rows

# archived season snapshot (2016-17 .. current) from the vaastav mirror
def load_fpl_season(season):
    players = list(csv.DictReader(io.StringIO(fetch(f"{ARCHIVE}/{season}/players_raw.csv"))))
    id2name = team_names(season)
    return rows_from_elements(players, id2name, season)

# live current season straight from the official FPL API (run in CI)
FPL_LIVE = "https://fantasy.premierleague.com/api/bootstrap-static/"
def load_fpl_live(season):
    boot = json.loads(fetch(FPL_LIVE))
    id2name = {str(t["id"]): t["name"] for t in boot["teams"]}
    return rows_from_elements(boot["elements"], id2name, season)

# ---- z-scoring -------------------------------------------------------------
def zmap(rows, key):
    vals = [r[key] for r in rows]
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)) or 1.0
    return {id(r): (r[key] - m) / sd for r in rows}

# position-specific weightings over z-scored per-90 metrics
WEIGHTS = {
    "GK":  {"sav90":0.9, "cs_rate":0.8, "inf90":0.6, "bps90":0.5, "gc90":-0.6},
    "DEF": {"cs_rate":0.9, "bps90":0.8, "inf90":0.5, "g90":0.5, "a90":0.4, "thr90":0.2, "gc90":-0.4},
    "MID": {"g90":0.8, "a90":0.7, "cre90":0.6, "thr90":0.6, "inf90":0.5, "bps90":0.4},
    "FWD": {"g90":1.0, "a90":0.6, "thr90":0.7, "cre90":0.4, "inf90":0.3},
}

def rate_season_group(rows):
    """rows = all players of one season+position. Returns rows with seasonRating."""
    if len(rows) < 4:
        for r in rows: r["seasonRating"] = 62  # too few to rank; neutral
        return rows
    keys = set(k for w in WEIGHTS.values() for k in w) | {"minutes"}
    Z = {k: zmap(rows, k) for k in keys if all(k in r for r in rows)}
    comps = []
    for r in rows:
        w = WEIGHTS[r["pos"]]
        perf = sum(wt * Z.get(k, {}).get(id(r), 0.0) for k, wt in w.items())
        total = perf + VOL_W * Z["minutes"][id(r)]
        comps.append((total, r))
    comps.sort(key=lambda x: x[0])
    n = len(comps)
    for i, (_, r) in enumerate(comps):
        pct = i / (n - 1)
        r["seasonRating"] = round(RAT_LO + (RAT_HI - RAT_LO) * (pct ** GAMMA))
    return rows

def rate_all(rows):
    # group by (season,pos), rate, then compute prime per player code
    groups = {}
    for r in rows:
        groups.setdefault((r["season"], r["pos"]), []).append(r)
    for g in groups.values():
        rate_season_group(g)
    prime = {}
    for r in rows:
        c = r["code"]
        prime[c] = max(prime.get(c, 0), r["seasonRating"])
    out = []
    for r in rows:
        out.append({
            "player": r["player"], "club": r["club"], "season": r["season"],
            "position": r["pos"], "seasonRating": r["seasonRating"],
            "primeRating": prime[r["code"]],
        })
    out.sort(key=lambda x: (x["club"], x["season"], -x["seasonRating"]))
    return out

def main():
    # modes: "archive" (default, reproducible POC from the mirror)
    #        "prod"    (CI: live current season + archived past + FBref history)
    mode = sys.argv[1] if len(sys.argv) > 1 else "archive"
    current = SEASONS[-1]
    past = SEASONS if mode == "archive" else SEASONS[:-1]

    rows = []
    for s in past:
        sys.stderr.write(f"loading {s} (archive) ... ")
        try:
            rs = load_fpl_season(s); rows += rs
            sys.stderr.write(f"{len(rs)} players\n")
        except Exception as e:
            sys.stderr.write(f"skip ({e})\n")

    if mode == "prod":
        sys.stderr.write(f"loading {current} (live FPL API) ... ")
        rs = load_fpl_live(current); rows += rs
        sys.stderr.write(f"{len(rs)} players\n")
        # deep history (1992-2016) produced by fbref_history.py, same row shape
        if os.path.exists("history_rows.json"):
            hr = json.load(open("history_rows.json", encoding="utf-8"))
            rows += hr
            sys.stderr.write(f"loaded {len(hr)} historical rows from FBref\n")

    out = rate_all(rows)
    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    sys.stderr.write(f"\nwrote players.json: {len(out)} player-seasons, "
                     f"{len(set(r['club'] for r in out))} clubs, "
                     f"{len(set(r['season'] for r in out))} seasons\n")

if __name__ == "__main__":
    main()
