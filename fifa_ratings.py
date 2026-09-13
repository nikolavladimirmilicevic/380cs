#!/usr/bin/env python3
"""
38-0 ratings from EA FC / FIFA overalls (sofifa), all editions FIFA 07 .. FC 26.

38-0's ratings are quality/perception ratings, close to a FIFA overall rather
than to statistical output (Leicester 2015-16 won the league with modest FIFA
ratings). So we use the overall directly:

    seasonRating = overall in that edition
    primeRating  = that player's highest overall across all editions

Edition year Y -> PL season (Y-1)-(Y). FIFA 07 -> 2006-07, FC 26 -> 2025-26.

Single source: mzafram2001/ea-fc (open, sofifa-sourced, auto-updated), one CSV
per edition with a consistent schema and a stable sofifa_id across editions.
Rows are filtered to the clubs that were actually in the Premier League each
season (PL_MEMBERSHIP, from openfootball/england).

Output matches the app schema: {player, club, season, position, seasonRating, primeRating}

Not covered: seasons before 2006-07 (no clean per-player overalls that far back).
Reconstructing them needs historical squad rosters, which this source lacks.
"""

import csv, io, json, re, sys, urllib.request

EAFC_BASE = "https://raw.githubusercontent.com/mzafram2001/ea-fc/main/data"
EDITIONS = ([("dataset_fifa_%02d.csv" % y, 2000 + y) for y in range(7, 24)]
            + [("dataset_ea_fc_%02d.csv" % y, 2000 + y) for y in (24, 25, 26)])

# club name (any spelling) -> canonical short label used by the app
CLUB = {
    "Arsenal":"Arsenal", "Aston Villa":"Aston Villa", "Barnsley":"Barnsley",
    "Birmingham City":"Birmingham", "Blackburn Rovers":"Blackburn", "Blackpool":"Blackpool",
    "Bolton Wanderers":"Bolton", "AFC Bournemouth":"Bournemouth", "Bournemouth":"Bournemouth",
    "Bradford City":"Bradford", "Brighton & Hove Albion":"Brighton", "Brentford":"Brentford",
    "Burnley":"Burnley", "Cardiff City":"Cardiff", "Charlton Athletic":"Charlton",
    "Chelsea":"Chelsea", "Coventry City":"Coventry", "Crystal Palace":"Crystal Palace",
    "Derby County":"Derby", "Everton":"Everton", "Fulham":"Fulham",
    "Huddersfield Town":"Huddersfield", "Hull City":"Hull", "Ipswich Town":"Ipswich",
    "Leeds United":"Leeds", "Leicester City":"Leicester", "Liverpool":"Liverpool",
    "Luton Town":"Luton", "Manchester City":"Man City", "Manchester United":"Man Utd",
    "Middlesbrough":"Middlesbrough", "Newcastle United":"Newcastle", "Norwich City":"Norwich",
    "Nottingham Forest":"Nott'm Forest", "Oldham Athletic":"Oldham", "Portsmouth":"Portsmouth",
    "Queens Park Rangers":"QPR", "Reading":"Reading", "Sheffield United":"Sheffield Utd",
    "Sheffield Wednesday":"Sheffield Weds", "Southampton":"Southampton", "Stoke City":"Stoke",
    "Sunderland":"Sunderland", "Swansea City":"Swansea", "Swindon Town":"Swindon",
    "Tottenham Hotspur":"Spurs", "Watford":"Watford", "West Bromwich Albion":"West Brom",
    "West Ham United":"West Ham", "Wigan Athletic":"Wigan", "Wimbledon":"Wimbledon",
    "Wolverhampton Wanderers":"Wolves",
}

PL_MEMBERSHIP = {
    "2006-07": ['Arsenal', 'Aston Villa', 'Blackburn', 'Bolton', 'Charlton', 'Chelsea', 'Everton', 'Fulham', 'Liverpool', 'Man City', 'Man Utd', 'Middlesbrough', 'Newcastle', 'Portsmouth', 'Reading', 'Sheffield Utd', 'Spurs', 'Watford', 'West Ham', 'Wigan'],
    "2007-08": ['Arsenal', 'Aston Villa', 'Birmingham', 'Blackburn', 'Bolton', 'Chelsea', 'Derby', 'Everton', 'Fulham', 'Liverpool', 'Man City', 'Man Utd', 'Middlesbrough', 'Newcastle', 'Portsmouth', 'Reading', 'Spurs', 'Sunderland', 'West Ham', 'Wigan'],
    "2008-09": ['Arsenal', 'Aston Villa', 'Blackburn', 'Bolton', 'Chelsea', 'Everton', 'Fulham', 'Hull', 'Liverpool', 'Man City', 'Man Utd', 'Middlesbrough', 'Newcastle', 'Portsmouth', 'Spurs', 'Stoke', 'Sunderland', 'West Brom', 'West Ham', 'Wigan'],
    "2009-10": ['Arsenal', 'Aston Villa', 'Birmingham', 'Blackburn', 'Bolton', 'Burnley', 'Chelsea', 'Everton', 'Fulham', 'Hull', 'Liverpool', 'Man City', 'Man Utd', 'Portsmouth', 'Spurs', 'Stoke', 'Sunderland', 'West Ham', 'Wigan', 'Wolves'],
    "2010-11": ['Arsenal', 'Aston Villa', 'Birmingham', 'Blackburn', 'Blackpool', 'Bolton', 'Chelsea', 'Everton', 'Fulham', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Spurs', 'Stoke', 'Sunderland', 'West Brom', 'West Ham', 'Wigan', 'Wolves'],
    "2011-12": ['Arsenal', 'Aston Villa', 'Blackburn', 'Bolton', 'Chelsea', 'Everton', 'Fulham', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Norwich', 'QPR', 'Spurs', 'Stoke', 'Sunderland', 'Swansea', 'West Brom', 'Wigan', 'Wolves'],
    "2012-13": ['Arsenal', 'Aston Villa', 'Chelsea', 'Everton', 'Fulham', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Norwich', 'QPR', 'Reading', 'Southampton', 'Spurs', 'Stoke', 'Sunderland', 'Swansea', 'West Brom', 'West Ham', 'Wigan'],
    "2013-14": ['Arsenal', 'Aston Villa', 'Cardiff', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Hull', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Norwich', 'Southampton', 'Spurs', 'Stoke', 'Sunderland', 'Swansea', 'West Brom', 'West Ham'],
    "2014-15": ['Arsenal', 'Aston Villa', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Hull', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'QPR', 'Southampton', 'Spurs', 'Stoke', 'Sunderland', 'Swansea', 'West Brom', 'West Ham'],
    "2015-16": ['Arsenal', 'Aston Villa', 'Bournemouth', 'Chelsea', 'Crystal Palace', 'Everton', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Norwich', 'Southampton', 'Spurs', 'Stoke', 'Sunderland', 'Swansea', 'Watford', 'West Brom', 'West Ham'],
    "2016-17": ['Arsenal', 'Bournemouth', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Hull', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Middlesbrough', 'Southampton', 'Spurs', 'Stoke', 'Sunderland', 'Swansea', 'Watford', 'West Brom', 'West Ham'],
    "2017-18": ['Arsenal', 'Bournemouth', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Huddersfield', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Southampton', 'Spurs', 'Stoke', 'Swansea', 'Watford', 'West Brom', 'West Ham'],
    "2018-19": ['Arsenal', 'Bournemouth', 'Brighton', 'Burnley', 'Cardiff', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Huddersfield', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Southampton', 'Spurs', 'Watford', 'West Ham', 'Wolves'],
    "2019-20": ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Norwich', 'Sheffield Utd', 'Southampton', 'Spurs', 'Watford', 'West Ham', 'Wolves'],
    "2020-21": ['Arsenal', 'Aston Villa', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Leeds', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Sheffield Utd', 'Southampton', 'Spurs', 'West Brom', 'West Ham', 'Wolves'],
    "2021-22": ['Arsenal', 'Aston Villa', 'Brentford', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Leeds', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', 'Norwich', 'Southampton', 'Spurs', 'Watford', 'West Ham', 'Wolves'],
    "2022-23": ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Leeds', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', "Nott'm Forest", 'Southampton', 'Spurs', 'West Ham', 'Wolves'],
    "2023-24": ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Liverpool', 'Luton', 'Man City', 'Man Utd', 'Newcastle', "Nott'm Forest", 'Sheffield Utd', 'Spurs', 'West Ham', 'Wolves'],
    "2024-25": ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Ipswich', 'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', "Nott'm Forest", 'Southampton', 'Spurs', 'West Ham', 'Wolves'],
    "2025-26": ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Leeds', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle', "Nott'm Forest", 'Spurs', 'Sunderland', 'West Ham', 'Wolves'],
}

def canon_club(name):
    n = (name or "").strip()
    for suf in (" FC", " AFC"):
        if n.endswith(suf): n = n[:-len(suf)].strip()
    if n.startswith("AFC ") and n[4:] in CLUB: return CLUB[n[4:]]
    return CLUB.get(n) or CLUB.get((name or "").strip())

DEFP = {"CB","LB","RB","LWB","RWB","SW","RCB","LCB"}
FWDP = {"ST","CF","LW","RW","LF","RF","SS","LS","RS","LWF","RWF"}
def pos_group(positions):
    first = re.split(r"[/,]", (positions or "").strip())[0].strip().upper()
    if first == "GK": return "GK"
    if first in DEFP: return "DEF"
    if first in FWDP: return "FWD"
    return "MID"

def season_label(year):
    y = int(year); return f"{y-1}-{str(y)[-2:]}"

def read_csv(path):
    if path.startswith("http"):
        with urllib.request.urlopen(path, timeout=120) as r:
            return csv.DictReader(io.StringIO(r.read().decode("utf-8-sig", "replace")))
    return csv.DictReader(open(path, encoding="utf-8-sig", errors="replace"))

def load_edition(fname, year, base=EAFC_BASE):
    season = season_label(year)
    members = PL_MEMBERSHIP.get(season)
    rows = []
    for r in read_csv(f"{base}/{fname}"):
        club = canon_club(r.get("club_name"))
        if not club or (members and club not in members):
            continue
        try: ov = int(float(r.get("overall")))
        except (ValueError, TypeError): continue
        rows.append({
            "pid": r.get("sofifa_id") or (r.get("short_name","")+r.get("long_name","")),
            "name": (r.get("alias") or r.get("short_name") or r.get("long_name") or "").strip(),
            "club": club, "season": season,
            "pos": pos_group(r.get("positions")), "ovr": ov,
        })
    return rows

def build(base=EAFC_BASE):
    rows = []
    for fname, year in EDITIONS:
        sys.stderr.write(f"loading {fname} ({season_label(year)}) ... ")
        try:
            rs = load_edition(fname, year, base); rows += rs
            sys.stderr.write(f"{len(rs)} PL players\n")
        except Exception as e:
            sys.stderr.write(f"skip ({e})\n")
    prime = {}
    for r in rows:
        if r["ovr"] > prime.get(r["pid"], 0): prime[r["pid"]] = r["ovr"]
    out = [{
        "player": r["name"], "club": r["club"], "season": r["season"],
        "position": r["pos"], "seasonRating": r["ovr"], "primeRating": prime[r["pid"]],
    } for r in rows]
    out.sort(key=lambda x: (x["club"], x["season"], -x["seasonRating"]))
    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    ss = sorted(set(x["season"] for x in out))
    sys.stderr.write(f"\nwrote players.json: {len(out)} player-seasons, "
                     f"{len(set(x['club'] for x in out))} clubs, "
                     f"{len(ss)} seasons ({ss[0]}..{ss[-1]})\n")

if __name__ == "__main__":
    build()
