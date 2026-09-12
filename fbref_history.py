#!/usr/bin/env python3
"""
FBref historical ingester (1992-93 .. 2015-16) -> history_rows.json

Runs in CI only. FBref cannot be fetched from a browser or from a restricted
sandbox, so this is the piece that GitHub Actions runs to extend coverage back
before the FPL era. It emits rows in the SAME intermediate shape that
build_ratings.rows_from_elements produces, so rate_all() rates old and new
seasons with one model.

Coverage note (be honest with yourself here): for these seasons FBref exposes
essentially standard stats only (goals, assists, minutes, position). There is
no clean-sheet / save / defensive-action data, so historical defender and
goalkeeper ratings lean mostly on availability and are the weak point of the
model. Tune, or blend in a positional prior, if you want them sharper. Advanced
tables (defensive actions, keeper stats) exist on FBref from ~2017-18, i.e. the
FPL era this file does not cover.

Requires: pip install soccerdata pandas
"""

import json, re, sys

REL_K = 6.0  # keep in sync with build_ratings.REL_K

SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1992, 2016)]  # 1992-93 .. 2015-16
POS_MAP = {"GK": "GK", "DF": "DEF", "MF": "MID", "FW": "FWD"}

def slug(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def to_pos(p):
    if not isinstance(p, str) or not p:
        return "MID"
    return POS_MAP.get(p.split(",")[0].strip(), "MID")

def col(row, *cands):
    """Pull the first present column from a flattened FBref row."""
    for c in cands:
        if c in row and row[c] == row[c]:  # not NaN
            return row[c]
    return 0

def main():
    import soccerdata as sd
    all_rows = []
    for season in SEASONS:
        try:
            fb = sd.FBref(leagues="ENG-Premier League", seasons=season)
            df = fb.read_player_season_stats(stat_type="standard")
        except Exception as e:
            sys.stderr.write(f"skip {season}: {e}\n")
            continue
        df = df.reset_index()
        df.columns = ["_".join([str(x) for x in c if x]) if isinstance(c, tuple) else str(c)
                      for c in df.columns]
        for _, r in df.iterrows():
            row = r.to_dict()
            minutes = float(col(row, "Playing Time_Min", "Min", "minutes") or 0)
            if minutes < 1:
                continue
            n90 = minutes / 90.0
            rel = n90 / (n90 + REL_K)
            goals = float(col(row, "Performance_Gls", "Gls", "goals") or 0)
            assists = float(col(row, "Performance_Ast", "Ast", "assists") or 0)
            player = col(row, "player", "Player") or ""
            club = col(row, "team", "Squad", "Team") or ""
            all_rows.append({
                "code": "hist:" + slug(player),   # links a player's own historical seasons
                "player": player,
                "club": club,
                "season": season,
                "pos": to_pos(col(row, "pos", "Pos")),
                "minutes": minutes,
                "g90": (goals / n90) * rel,
                "a90": (assists / n90) * rel,
                # no defensive / keeper / index stats available this far back
            })
        sys.stderr.write(f"{season}: {len(all_rows)} rows so far\n")

    with open("history_rows.json", "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False)
    sys.stderr.write(f"wrote history_rows.json: {len(all_rows)} rows\n")

if __name__ == "__main__":
    main()
