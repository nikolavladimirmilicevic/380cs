#!/usr/bin/env python3
"""
Parse 380db.txt (raw text copied from 38-0.app squad screens) into players.json.

Each squad section in the scrape looks like:
    ... UI lines ...
    West Ham United        <- club
    2010/11                <- season (YYYY/YY)
    ... UI lines ...
    82                     <- rating
    Scott Parker           <- name
    England                <- nationality
    CM                     <- positions (1-3 lines)
    CDM
    RM
    <blank>
    79
    Demba Ba
    ...

Output rows (app schema): {player, club, season, position, seasonRating, primeRating}
The game shows one rating per player (the season rating), so primeRating is set
equal to seasonRating until prime-mode ratings are also scraped.

Usage: python parse_scrape.py            # reads 380db.txt -> writes players.json
"""
import re, json, sys

CLUB = {
    "Arsenal":"Arsenal","Aston Villa":"Aston Villa","Barnsley":"Barnsley",
    "Birmingham City":"Birmingham","Blackburn Rovers":"Blackburn","Blackpool":"Blackpool",
    "Bolton Wanderers":"Bolton","AFC Bournemouth":"Bournemouth","Bournemouth":"Bournemouth",
    "Bradford City":"Bradford","Brighton & Hove Albion":"Brighton","Brentford":"Brentford",
    "Burnley":"Burnley","Cardiff City":"Cardiff","Charlton Athletic":"Charlton",
    "Chelsea":"Chelsea","Coventry City":"Coventry","Crystal Palace":"Crystal Palace",
    "Derby County":"Derby","Everton":"Everton","Fulham":"Fulham",
    "Huddersfield Town":"Huddersfield","Hull City":"Hull","Ipswich Town":"Ipswich",
    "Leeds United":"Leeds","Leicester City":"Leicester","Liverpool":"Liverpool",
    "Luton Town":"Luton","Manchester City":"Man City","Manchester United":"Man Utd",
    "Middlesbrough":"Middlesbrough","Newcastle United":"Newcastle","Norwich City":"Norwich",
    "Nottingham Forest":"Nott'm Forest","Oldham Athletic":"Oldham","Portsmouth":"Portsmouth",
    "Queens Park Rangers":"QPR","Reading":"Reading","Sheffield United":"Sheffield Utd",
    "Sheffield Wednesday":"Sheffield Weds","Southampton":"Southampton","Stoke City":"Stoke",
    "Sunderland":"Sunderland","Swansea City":"Swansea","Swindon Town":"Swindon",
    "Tottenham Hotspur":"Spurs","Watford":"Watford","West Bromwich Albion":"West Brom",
    "West Ham United":"West Ham","Wigan Athletic":"Wigan","Wimbledon":"Wimbledon",
    "Wolverhampton Wanderers":"Wolves",
    "West Ham":"West Ham","Tottenham":"Spurs","Sheffield Wed":"Sheffield Weds",
    "Newcastle Utd":"Newcastle","Bradford":"Bradford","Leeds":"Leeds","Derby":"Derby",
    "Leicester":"Leicester","Coventry":"Coventry",
}
def canon(name):
    n=(name or "").strip()
    for suf in (" FC"," AFC"):
        if n.endswith(suf): n=n[:-len(suf)].strip()
    if n.startswith("AFC ") and n[4:] in CLUB: return CLUB[n[4:]]
    return CLUB.get(n) or CLUB.get((name or "").strip())

DEFP={"CB","LB","RB","LWB","RWB","SW"}
FWDP={"ST","CF","LW","RW","LF","RF","SS"}
def posg(p):
    p=(p or "").upper()
    if p=="GK": return "GK"
    if p in DEFP: return "DEF"
    if p in FWDP: return "FWD"
    return "MID"
POS={"GK","CB","LB","RB","LWB","RWB","SW","CDM","DM","CM","CAM","LM","RM","LW","RW","ST","CF","SS","LF","RF"}

def parse(path):
    lines=[l.rstrip("\r\n").strip() for l in open(path,encoding="utf-8",errors="replace")]
    idx=[]
    for i,l in enumerate(lines):
        if re.match(r'^\d{4}/\d{2}$', l):
            j=i-1
            while j>=0 and not lines[j]: j-=1
            idx.append((i, lines[j] if j>=0 else "", l))
    rows=[]; report=[]; unmapped=set()
    for k,(i,club_raw,season_raw) in enumerate(idx):
        end=idx[k+1][0]-1 if k+1<len(idx) else len(lines)
        body=lines[i+1:end]
        club=canon(club_raw)
        season=season_raw[:4]+"-"+season_raw[5:7]
        if not club: unmapped.add(club_raw); continue
        n=0; p=0
        while p<len(body):
            if re.match(r'^[3-9]\d$', body[p]):
                rating=int(body[p]); q=p+1
                while q<len(body) and not body[q]: q+=1
                name=body[q] if q<len(body) else ""
                r=q+1
                if r<len(body) and body[r] and body[r] not in POS: r+=1
                poss=[]
                while r<len(body) and body[r] in POS: poss.append(body[r]); r+=1
                if name and not re.match(r'^[3-9]\d$', name):
                    rows.append({"player":name,"club":club,"season":season,
                                 "position":posg(poss[0]) if poss else "MID",
                                 "seasonRating":rating,"primeRating":rating})
                    n+=1
                p=max(r,q+1)
            else: p+=1
        report.append((club,season,n))
    return rows,report,unmapped

def main():
    src=sys.argv[1] if len(sys.argv)>1 else "380db.txt"
    rows,report,unmapped=parse(src)
    rows.sort(key=lambda x:(x["club"],x["season"],-x["seasonRating"]))
    json.dump(rows, open("players.json","w",encoding="utf-8"), ensure_ascii=False, separators=(",",":"))
    sys.stderr.write(f"parsed {len(report)} club-seasons, {len(rows)} players -> players.json\n")
    if unmapped: sys.stderr.write("UNMAPPED clubs: "+", ".join(sorted(unmapped))+"\n")

if __name__=="__main__": main()
