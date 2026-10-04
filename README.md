# Abi 2027 – Ziel 15 Punkte

Privates Arbeits-Repo für Luiz' Schuljahr bis zum Abitur (Werkgymnasium Heidenheim, Abi 2027). Jeder Lernblock ist ein Issue mit Story Points, jede Woche gibt es einen Test, und was nicht gelernt wurde, wird automatisch in die nächste Woche geschoben.

Zwei Phasen im selben System:

| Phase | Zeitraum | Wochen | Stories | Epic |
|---|---|---|---|---|
| **Klausuren 1. Halbjahr** | 05.10.–20.12.2026 | K01–K11 | KL-001 … | E07, Milestones = Klausuren K01–K11 |
| **Abiturvorbereitung** | 04.01.–30.06.2027 | W01–W24 | US-001 … | E01–E06, Milestones M01–M10 |

## „Bearbeite diesen Termin“

Jeder Kalendertermin enthält ein vollständiges Briefing (erzeugt in `data/kalender.json`): Ziel, Luiz' Aufgaben, was Claude vorbereitet und raussucht, Material, welche Infos noch fehlen, und wann der Block erledigt ist. Luiz schreibt nur **„bearbeite diesen Termin“** – Claude:

1. nimmt den Lernblock, der gerade läuft oder als Nächstes kommt (oder den genannten), und liest Beschreibung + Issue (ID `KL-…`/`US-…`),
2. klärt zuerst die Punkte unter **❓ Braucht Claude von dir**, falls sie nicht schon im Lernplan-Status stehen,
3. arbeitet die Schritte unter **🤖** ab und legt ein Aufgabenblatt vor (Aufgaben mit Quelle/Link und Zeitvorgabe, Lösungen erst nach der Abgabe),
4. korrigiert, ergänzt die Fehlerliste, hakt das Issue ab und trägt neue Infos in Repo, Kalender und Lernplan-Status nach.

## Klausuren 1. Halbjahr (Okt–Dez 2026)

Mathe 09.11. · Physik 12.11. · Kunst 17.11. · Geschichte 23.11. · Englisch 26.11. · Deutsch 03.12. · Gemeinschaftskunde 07.12. · Sport 11.12. · Religion 14.12. · Physik 17.12. · Mathe 21.12. – Details in [docs/plan.md](docs/plan.md) und [docs/wochen/K01.md](docs/wochen/K01.md) ff.

## Abiturprüfungen

| Datum | Prüfung | Epic |
|---|---|---|
| Mo 19.04.2027 | Sport schriftlich (Klausur 240 Min + Praxis) | E03 |
| Di 20.04.2027 | Physik schriftlich (300 Min, 3 von 4 Aufgaben) | E02 |
| Mi 05.05.2027 | Mathe schriftlich (Teil A ohne Hilfsmittel + Teil B) | E01 |
| 28.–30.06.2027 | Deutsch und Religion mündlich | E04, E05 |

## Aufbau

| | |
|---|---|
| **Epics** | 7 – eins pro Abi-Prüfungsfach, Organisation, Klausuren 1. Halbjahr |
| **Lernblöcke (Stories)** | 185 Issues mit Label `type:lernblock` (75 Klausurphase, 110 Abi), je mit Termin, Aufgaben, Briefing und Story Points |
| **Story Points** | 528 gesamt: 1 SP ≤ 45 Min · 2 SP = 60 Min · 3 SP = 90 Min · 5 SP = 2–2,5 h · 8 SP = Generalprobe |
| **Milestones** | 21 – die 11 Klausuren (K01–K11) und 10 Abi-Meilensteine (M01–M10) |
| **Wochen** | 35 – Label `woche:K01` … `woche:K11` und `woche:W01` … `woche:W24` |

Übersicht: [docs/plan.md](docs/plan.md) · [docs/milestones.md](docs/milestones.md) · Wochen: [docs/wochen/](docs/wochen/) · Regeln: [docs/regeln.md](docs/regeln.md)

Der Kalender (Google) zeigt dieselben Blöcke mit dem Briefing aus `data/kalender.json`; die Notion-Seite „Abi-Lernplan 2027“ die Abi-Wochen. Abgehakt wird hier.

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
python3 scripts/generate.py   # erzeugt data/*.json (inkl. kalender.json) und docs/
python3 scripts/validate.py   # prüft den Plan
python3 -m unittest discover -s tests
```

Nach dem Push auf `main` legt die Action fehlende Issues und Milestones an (ohne laufende Actions: `GITHUB_REPOSITORY=luizz28-goat/abi-2027 python3 scripts/bootstrap.py` mit Token). Danach die geänderten Termine aus `data/kalender.json` in den Google Kalender übernehmen. Wochenstart und -abschluss lassen sich unter *Actions → Wochentest und Wochenabschluss → Run workflow* auch von Hand auslösen.

## Datenschutz

Keine Noten, Zeugnisse oder persönlichen Dokumente ins Repo. Ergebnisse der Generalproben nur als „≥ 13 Punkte ja/nein“ im Wochentest.
