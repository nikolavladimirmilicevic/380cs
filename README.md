# 38-0 Cheat Sheet

Rejtinzi igraca za draft u igri 38-0, bazirani na EA FC / FIFA overall oceni.
Za izabrani tim i sezonu daje dve opadajuce liste: rejting u toj sezoni i rejting
u prajmu.

## Zasto FIFA overall

38-0 ocenjuje "koliko je igrac dobar", sto je mnogo blize FIFA overall oceni nego
statistici ucinka. Leicester 2015-16 osvaja ligu, a Mahrez, Vardy i Kante te
sezone imaju skromne FIFA ocene, bas kao sto ih ni 38-0 verovatno ne bi visoko
ocenio. Zato:

    seasonRating = FIFA overall u toj ediciji
    primeRating  = najveci overall tog igraca kroz sve edicije

Edicija FIFA Y = PL sezona (Y-1)-(Y). FIFA 07 -> 2006-07, FC 26 -> 2025-26.

## Sta je unutra

`players.json`: 12404 PL igrac-sezona, 44 kluba, sve sezone 2006-07 do 2025-26,
neprekidno. Samo klub-sezone koje su STVARNO bile u Premijer ligi te godine
(spisak lige po sezoni iz openfootball/england je ugradjen u pipeline).

## Izvor

Jedan dosledan izvor: `mzafram2001/ea-fc` (otvoren, sa sofifa, auto-osvezavan),
po jedan CSV za svaku ediciju FIFA 07 do FC 26, sa stabilnim `sofifa_id` kroz
edicije (za prajm). `fifa_ratings.py` povlaci sve edicije, filtrira na PL i pravi
`players.json`. Koristi samo standardnu biblioteku, bez ijedne zavisnosti.

```
python fifa_ratings.py
```

## Deploy (GitHub Pages)

1. Ubaci `index.html` i `players.json` u repo (isti folder), upali Pages
   (Settings > Pages > Deploy from a branch > main > /root).
2. Otvori stranicu; aplikacija sama ucita `players.json`.

## Osvezavanje (opciono)

`.github/workflows/refresh.yml` jednom mesecno (i na rucno pokretanje) povuce
najnovije ocene, regenerise `players.json` i commituje ako ima promene. Da bi bot
smeo da commituje: Settings > Actions > General > Workflow permissions > Read and
write permissions.

FIFA overali se ne menjaju iz dana u dan, pa mesecno je sasvim dovoljno. Kad
izadje nova edicija (FC 27), dodaj je u listu `EDITIONS` na vrhu skripte.

## Sezone pre 2006-07

Prave FIFA ocene ne postoje toliko unazad. FIFA 05 i 06 (2004-05, 2005-06) mogu
da se dodaju iz fifaindex seta ako zatreba (prava, ne rekonstruisana, data). Za
sezone pre 2004 ne postoji upotrebljiv izvor overall ocena, pa bi rekonstrukcija
trazila istorijske sastave (rostere) plus procenu ocene, sto je poseban posao.

## Fajlovi

- `index.html` - aplikacija
- `players.json` - FIFA-bazirani rejtinzi (2006-07..2025-26)
- `fifa_ratings.py` - pipeline (bez zavisnosti)
- `.github/workflows/refresh.yml` - mesecno osvezavanje (opciono)
