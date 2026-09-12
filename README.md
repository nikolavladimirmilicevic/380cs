# 38-0 Cheat Sheet

Sopstvena procena rejtinga igrača za draft u igri 38-0, iz prave statistike, sa
dve opadajuce rang-liste po klub-sezoni: rejting u toj sezoni i rejting u prajmu.
Ne prepisuje tudje rejtinge, racuna svoje.

## Kako radi (arhitektura)

```
FBref (1992-2016)  ─┐
                    ├─►  build_ratings.py  ─►  players.json  ─►  cheatsheet.html
FPL API (tekuca)   ─┘        (model)          (na GitHub Pages)     (u browseru)
```

- `build_ratings.py` skuplja statistiku, propušta je kroz model i pravi jedan
  `players.json`.
- GitHub Action (`.github/workflows/ratings.yml`) ga pokrece po rasporedu i
  commituje osveženi `players.json`.
- `cheatsheet.html` pri otvaranju sam povuce `players.json` sa istog origina
  (nema CORS-a), pa je uvek aktuelan. Ako fajl nije dostupan, pada na keš pa na
  ugradjeni demo. Rucno ucitavanje (nalepi / fajl / URL) i dalje radi.

Svežina je bitna samo za tekucu sezonu. Stare sezone su zamrznute i racunaju se
jednom.

## Sta je vec tu (POC)

`players.json` u ovom paketu je stvaran, izracunat rezultat za sezone
2016-17 do 2025-26 (FPL podaci), 5343 igrač-sezona, 34 kluba. Nije demo i nije
prepisan. Otvori `cheatsheet.html`, klikni "Otvori .json fajl" i izaberi
`players.json` da odmah vidiš prave brojeve, ili hostuj oba fajla zajedno pa se
ucita sam.

## Deploy (GitHub Pages)

1. Ubaci `cheatsheet.html` i `players.json` u repo, upali Pages.
2. Otvori stranicu. Aplikacija sama ucita `players.json`.

Ako app i podaci nisu na istom mestu, promeni `DATA_URL` u `cheatsheet.html` na
punu adresu tvog `players.json`.

## Istorija + živa sezona (CI)

1. Upali Actions na repou.
2. Pokreni workflow rucno sa `rebuild_history = true` jednom, da se izgradi
   `fbref_history.py` -> `history_rows.json` (1992-2016). To se commituje i
   koristi dalje.
3. Dnevni cron posle toga radi `build_ratings.py prod`: arhiva proših sezona +
   živa tekuca sezona sa FPL API-ja + commitovana istorija, pa commituje novi
   `players.json`.

Lokalno / rucno:
```
python build_ratings.py          # POC: samo FPL arhiva 2016-17..danas
python build_ratings.py prod     # živa tekuca sezona + istorija ako postoji
```

## Model i podešavanje

Za svaku klub-sezonu, po poziciji: težinski zbir per-90 ucinaka (golovi,
asistencije, threat/creativity/influence, bps, odbrane, clean sheets, primljeni
golovi), umanjen za mali uzorak (shrink), plus faktor minutaže. Onda percentilno
mapiranje unutar sezone i pozicije u opseg ~47-97. Prajm je najbolja sezona
igrača u podacima.

Sve rucice su na vrhu `build_ratings.py`:
- `WEIGHTS` po poziciji je tvoja filozofija rejtinga, tu se najviše menja.
- `REL_K`, `VOL_W`, `RAT_LO`, `RAT_HI`, `GAMMA` oblikuju raspodelu.

## Iskreno o ogranicenjima

- Golmani i odbrana su najteži. U FPL eri postoje clean sheets, odbrane i bps
  koji pomažu; u FBref eri (pre 2016) ima samo osnovne statistike, pa su
  istorijski rejtinzi odbrane i golmana slabi (uglavnom minutaža). Za bolje,
  dodaj FBref napredne tabele gde postoje ili pozicioni prior.
- Skaliranje je percentilno unutar sezone, pa je najbolji na svakoj poziciji
  svake sezone ~97. Odlicno za rangiranje unutar sastava, slabije za poredjenje
  apsolutnog kvaliteta izmedju era.
- Identitet igrača izmedju FBref ere i FPL ere nije spojen, pa se prajm ne
  proteže preko 2016. za istog igrača. Za to treba crosswalk imena (TODO).
- FBref ima pravila korišcenja i rate limit. `soccerdata` kešira i usporava
  zahteve; ne skreči agresivno.

## Fajlovi

- `cheatsheet.html` - aplikacija (bez zavisnosti, hostuj bilo gde)
- `players.json` - izracunati rejtinzi (POC: 2016-17..2025-26)
- `build_ratings.py` - model i pipeline
- `fbref_history.py` - istorijski ingester (CI)
- `.github/workflows/ratings.yml` - osvežavanje
