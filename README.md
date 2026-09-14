# 38-0 Cheat Sheet (prave ocene)

Cheat sheet za draft u 38-0, sa PRAVIM ocenama iz igre (skrejpovane rucno).

## Fajlovi

- `index.html` - aplikacija. Izaberes tim i sezonu, dobijes dve opadajuce liste
  igraca: rejting u sezoni i rejting u prajmu. Ucitava `players.json`.
- `coverage-tracker.html` - tabla za skrejpovanje. Prati koje klub-sezone si vec
  uneo i sta fali, od svih 706 PL klub-sezona (1992-93 do 2026-27). Sve se cuva
  u pregledacu. Export daje JSON sa svim unetim podacima.
- `players.json` - baza ocena koju aplikacija cita. Pocinje prazna (`[]`) i puni
  se kako skrejpujes. Dok je prazna, aplikacija prikazuje ugradjeni demo.

## Tok rada

1. Otvori `coverage-tracker.html`, skrejpuj 38-0 klub-sezonu po klub-sezonu,
   lepi ocene i cuvaj. Tabla ti pokazuje sta jos fali.
2. Kad zavrsis rundu, Export -> posalji mi JSON.
3. Ja ga pretvorim u `players.json` (format aplikacije) i ti ga commitujes.
4. `index.html` ga ucita i prikazuje prave ocene.

## Deploy (GitHub Pages)

Ubaci fajlove u repo, upali Pages (Settings > Pages > main > /root). Aplikacija
je na `.../index.html`, tabla na `.../coverage-tracker.html`.
