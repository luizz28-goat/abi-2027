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
- Kalendertexte kommen aus `data/kalender.json` (Titel = `summary`, Beschreibung = `description`). Nach Planänderungen die
  betroffenen Google-Kalender-Termine mit genau diesen Texten aktualisieren.

## „Bearbeite diesen Termin“

Luiz schreibt oft nur diesen Satz. Dann:

1. Den Lernblock im Google Kalender finden, der gerade läuft oder als Nächstes kommt (oder den, den Luiz nennt).
   Die Beschreibung enthält die ID (`KL-…` Klausurphase, `US-…` Abi). Dazu das Issue mit dieser ID lesen.
2. Abschnitt „❓ Braucht Claude von dir“: erst im Projekt-Dokument `lernplan-status.md` bzw. `abi-lernplan-status.md`
   nachsehen; fehlt die Info, Luiz in einer Nachricht genau danach fragen.
3. Die Schritte unter „🤖“ der Reihe nach ausführen. Ergebnis für Luiz: ein Aufgabenblatt mit Quelle/Link,
   Aufgabennummer und Zeitvorgabe; Lösungen zurückhalten, bis er abgibt. Mathebattle läuft im Browser der Claude-App
   (Luiz ist dort angemeldet); nie Passwörter eingeben.
4. Nach der Abgabe korrigieren, Fehlerliste in Notion ergänzen, Aufgaben im Issue abhaken und Issue schließen,
   neue Infos (Klausurthemen usw.) in Status-Dokument, `data/` (z. B. Testfragen aufs echte Thema) und Kalender nachtragen.

## Offene Punkte (Stand 04.10.2026)

- GitHub Actions starten nicht: „account is locked due to a billing issue“ (Luiz muss unter github.com/settings/billing
  nachsehen). Bis dahin Bootstrap und Wochenstart/-abschluss von Hand bzw. per Claude ausführen:
  `GITHUB_REPOSITORY=luizz28-goat/abi-2027 python3 scripts/woche.py start|abschluss --woche K01`.
  Dafür läuft der geplante Task „Wochenabschluss abi-2027“ (So 19:50 Berlin): Abschluss der endenden Woche + Start der
  nächsten. Sobald die Actions wieder laufen, diesen Task löschen, sonst läuft alles doppelt.
- Klausurthemen fehlen noch für alle Fächer der Klausurphase (siehe „❓“ in den Terminen); Mathe 09.11. vermutlich Stochastik.
- Sport (Herr Werner): Praxis-Termine, Praxis-Wahl, Inhalte Teilkompetenzen 23/26/27 – Frage am 11.01.2027.
- Physik (Herr Baier): weitere prüfungsrelevante Kapitel? – Frage am 11.01.2027.
- Klausurplan 2. Halbjahr kommt im Februar 2027 – danach Blöcke anpassen.
