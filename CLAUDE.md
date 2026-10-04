# CLAUDE.md

## Arbeitsweise

- Repo von Luiz (luizz28-goat) für die Abi-Vorbereitung 2027. Luiz entscheidet über Inhalte.
- Gleicher Stil wie „Projekt Luiz in Space“: kanonische Daten in `data/lernbloecke.json` und `data/testfragen.json`,
  alles andere erzeugt `scripts/generate.py`. Generierte Dateien nie von Hand ändern.
- Vor jedem Commit: `python3 scripts/generate.py && python3 scripts/validate.py && python3 -m unittest discover -s tests`.
- Wenn sich der Plan ändert (neue Klausur, Block fällt aus, Thema bekannt), auch den Google Kalender und die Notion-Seite
  „Abi-Lernplan 2027“ anpassen, damit alle drei gleich sind.
- Labels `woche:*` und `nachholen` an bestehenden Issues gehören dem Wochenabschluss (`scripts/woche.py`); `bootstrap.py` ändert sie nicht.
- Keine Noten, Zeugnisse oder persönlichen Dokumente committen.
- Commit-Nachrichten auf Deutsch.

## Offene Punkte (Stand 04.10.2026)

- Sport (Herr Werner): Praxis-Termine, Praxis-Wahl, Inhalte Teilkompetenzen 23/26/27 – Frage am 11.01.2027.
- Physik (Herr Baier): weitere prüfungsrelevante Kapitel? – Frage am 11.01.2027.
- Klausurplan 2. Halbjahr kommt im Februar 2027 – danach Blöcke anpassen.
