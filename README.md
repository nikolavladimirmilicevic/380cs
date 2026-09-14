# 38-0 Cheat Sheet (prave ocene)

Cheat sheet za draft u 38-0, sa PRAVIM ocenama iz igre. Aplikacija cita tvoj
skrejp fajl `380db.txt` direktno i parsira ga u pregledacu, pa kad god dopunis i
pushujes taj fajl, novi podaci su odmah u aplikaciji. Nema medjukoraka.

## Fajlovi

- `index.html` - aplikacija. Izaberes tim i sezonu, dobijes dve opadajuce liste
  igraca (rejting u sezoni i u prajmu). Ucitava i parsira `380db.txt`.
- `380db.txt` - tvoj skrejp iz 38-0 (sirov tekst sa ekrana igre). Ovo je baza.
- `coverage-tracker.html` - tabla koja prati koje od svih 706 PL klub-sezona
  (1992-93 do 2026-27) si vec uneo i sta fali.

## Tok rada

1. Skrejpuj 38-0 klub-sezonu, nalepi u `380db.txt`, commituj i pushuj.
2. Aplikacija sama povuce novi `380db.txt` i prikaze prave ocene. Gotovo.

Format u `380db.txt` je onakav kakav ti igra da na ekranu: po sekciji klub, pa
sezona (npr. `2010/11`), pa blokovi igraca (rejting, ime, nacija, pozicije).
Parser sam preskace UI tekst, mapira klubove i pozicije, i cisti duplikate ako
istu klub-sezonu skrejpujes dvaput.

Napomena: igra prikazuje jedan rejting po igracu (sezonski), pa je prime zasad
izjednacen sa sezonskim. Ako skrejpujes i prime mod, javi pa razdvojimo.

## Deploy (GitHub Pages)

Fajlovi u repo, Pages upaljen (Settings > Pages > main > /root). Aplikacija je na
`.../index.html`, tabla na `.../coverage-tracker.html`.
