# Abi 2027 – Ziel 15 Punkte

Privates Arbeits-Repo für Luiz' Abiturvorbereitung (Werkgymnasium Heidenheim, Abi 2027). Jeder Lernblock ist ein Issue mit Story Points, jede Woche gibt es einen Test, und was nicht gelernt wurde, wird automatisch in die nächste Woche geschoben.

## Prüfungen

| Datum | Prüfung | Epic |
|---|---|---|
| Mo 19.04.2027 | Sport schriftlich (Klausur 240 Min + Praxis) | E03 |
| Di 20.04.2027 | Physik schriftlich (300 Min, 3 von 4 Aufgaben) | E02 |
| Mi 05.05.2027 | Mathe schriftlich (Teil A ohne Hilfsmittel + Teil B) | E01 |
| 28.–30.06.2027 | Deutsch und Religion mündlich | E04, E05 |

## Aufbau

| | |
|---|---|
| **Epics** | 6 – eins pro Prüfungsfach plus Organisation |
| **Lernblöcke (Stories)** | 110 Issues mit Label `type:lernblock`, je mit Termin, Aufgaben und Story Points |
| **Story Points** | 329 gesamt: 1 SP ≤ 45 Min · 2 SP = 60 Min · 3 SP = 90 Min · 5 SP = 2–2,5 h · 8 SP = Generalprobe |
| **Milestones** | 10 – von „Diagnose abgeschlossen“ (10.01.) bis „Abi geschafft“ (30.06.) |
| **Wochen** | 24 – Label `woche:W01` … `woche:W24` |

Übersicht: [docs/plan.md](docs/plan.md) · [docs/milestones.md](docs/milestones.md) · Wochen: [docs/wochen/](docs/wochen/) · Regeln: [docs/regeln.md](docs/regeln.md)

Der Kalender (Google) und die Notion-Seite „Abi-Lernplan 2027“ zeigen dieselben Blöcke. Abgehakt wird hier.

## Die Woche

1. **Montag früh** legt die Action das Issue **„Wochentest Wxx“** an – eine Frage zu jedem Block der Woche, auch zu nachgeholten.
2. **Unter der Woche:** Block erledigt → Aufgaben im Issue abhaken und Issue schließen.
3. **Sonntag 18 Uhr (Wochencheck):** Test ohne Unterlagen beantworten (oder Claude schicken und korrigieren lassen), dann nur die richtigen Fragen abhaken.
4. **Sonntag 20 Uhr** läuft der Wochenabschluss:
   - offene Blöcke und Blöcke mit falscher Testfrage → wieder offen, Label `nachholen`, in die nächste Woche verschoben,
   - die nächste Woche bekommt ein Issue **„Nachholblock“** mit den zusätzlichen Story Points und Terminvorschlägen,
   - Test-Ergebnis (bestanden ab 80 %) und Gesamtfortschritt im Issue **„📊 Fortschritt Abi 2027“**.

## Plan ändern

Lernblöcke stehen in `data/lernbloecke.json`, Testfragen in `data/testfragen.json`. Danach:

```bash
python3 scripts/generate.py   # erzeugt data/*.json und docs/
python3 scripts/validate.py   # prüft den Plan
python3 -m unittest discover -s tests
```

Nach dem Push auf `main` legt die Action fehlende Issues und Milestones an. Wochenstart und -abschluss lassen sich unter *Actions → Wochentest und Wochenabschluss → Run workflow* auch von Hand auslösen.

## Datenschutz

Keine Noten, Zeugnisse oder persönlichen Dokumente ins Repo. Ergebnisse der Generalproben nur als „≥ 13 Punkte ja/nein“ im Wochentest.
