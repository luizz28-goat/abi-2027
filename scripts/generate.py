#!/usr/bin/env python3
"""Kanonischer Generator für den Abi-Plan.

Eingaben (von Hand gepflegt):
  data/lernbloecke.json  – alle Lernblöcke (Datum, Zeit, Fach, Thema, Aufgaben, Woche, Art)
  data/testfragen.json   – eine Testfrage pro Lernblock (Schlüssel = Datum)

Ausgaben (generiert, nicht von Hand ändern):
  data/stories.json, data/epics.json, data/milestones.json, data/wochen.json, data/labels.json
  docs/plan.md, docs/milestones.md, docs/wochen/Wxx.md

Ablauf: python3 scripts/generate.py && python3 scripts/validate.py
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"

WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

EPICS = [
    {"id": "E01", "fach": "Mathe", "title": "Mathe-LF schriftlich (05.05.2027)", "ziel": "15 Punkte in der schriftlichen Mathe-Prüfung: Teil A sicher ohne Hilfsmittel, Teil B Analysis, Geometrie, Stochastik."},
    {"id": "E02", "fach": "Physik", "title": "Physik-LF schriftlich (20.04.2027)", "ziel": "15 Punkte in Physik: Felder, Induktion, Schwingungen und Wellen, Wellenoptik, Quanten- und Atomphysik."},
    {"id": "E03", "fach": "Sport", "title": "Sport-LF Klausur + Praxis (19.04.2027)", "ziel": "15 Punkte in der Sport-Klausur (Wissensbereiche 1 und 2) und Praxis auf Wertungstabellen-Niveau."},
    {"id": "E04", "fach": "Deutsch", "title": "Deutsch mündlich (28.–30.06.2027)", "ziel": "15 Punkte mündlich: Mario und der Zauberer, Woyzeck, Lyrik, Sachtexte und Sprache aus allen vier Halbjahren."},
    {"id": "E05", "fach": "Religion", "title": "Religion mündlich (28.–30.06.2027)", "ziel": "15 Punkte mündlich: Gottesfrage, Jesus Christus, Menschenbild, Ethik, Kirche aus allen vier Halbjahren."},
    {"id": "E06", "fach": "Organisation", "title": "Wochentests, Nachholen und Organisation", "ziel": "Jede Woche getestet, nichts bleibt liegen, offene Fragen an Lehrkräfte geklärt."},
]

MILESTONES = [
    {"id": "M01", "title": "Diagnose abgeschlossen", "due": "2027-01-10", "beschreibung": "Themen-Ampel für Mathe, Physik, Sport steht; Fehlerprotokolle angelegt."},
    {"id": "M02", "title": "Analysis + Felder/Induktion durch", "due": "2027-02-14", "beschreibung": "Mathe-Analysis komplett und Physik E-/B-Felder, Induktion, Schwingkreis einmal mit Abi-Aufgaben durchgearbeitet."},
    {"id": "M03", "title": "Geometrie + Schwingungen/Wellen durch", "due": "2027-02-28", "beschreibung": "Analytische Geometrie und Schwingungen/Wellen durchgearbeitet."},
    {"id": "M04", "title": "Stochastik, Optik, Quanten, Atom + Sport-Theorie durch", "due": "2027-03-21", "beschreibung": "Alle Prüfungsgebiete einmal durch, Sport-Wissensbereiche komplett."},
    {"id": "M05", "title": "Generalproben Osterferien", "due": "2027-04-04", "beschreibung": "Sport, Physik und Mathe je einmal komplett unter Prüfungszeit, ausgewertet."},
    {"id": "M06", "title": "Abi Sport", "due": "2027-04-19", "beschreibung": "Schriftliche Sport-Prüfung (Klausur + Praxis)."},
    {"id": "M07", "title": "Abi Physik", "due": "2027-04-20", "beschreibung": "Schriftliche Physik-Prüfung."},
    {"id": "M08", "title": "Abi Mathe", "due": "2027-05-05", "beschreibung": "Schriftliche Mathe-Prüfung."},
    {"id": "M09", "title": "Mündlich prüfungsbereit", "due": "2027-06-27", "beschreibung": "Deutsch und Religion je mind. zwei Probeprüfungen mit sicherem Vortrag."},
    {"id": "M10", "title": "Abi geschafft", "due": "2027-06-30", "beschreibung": "Mündliche Prüfungen Deutsch und Religion abgelegt."},
]

LABELS = [
    {"name": "type:epic", "color": "5319E7", "description": "Großes Ziel pro Fach"},
    {"name": "type:lernblock", "color": "1D76DB", "description": "Ein Lernblock (Story)"},
    {"name": "type:wochentest", "color": "0E8A16", "description": "Wöchentlicher Test"},
    {"name": "type:fortschritt", "color": "BFD4F2", "description": "Fortschritts-Übersicht"},
    {"name": "nachholen", "color": "B60205", "description": "Nicht erledigt oder Test nicht bestanden – in dieser Woche nachholen"},
    {"name": "generalprobe", "color": "8E44AD", "description": "Prüfung unter echten Bedingungen"},
    {"name": "fach:mathe", "color": "6F42C1", "description": ""},
    {"name": "fach:physik", "color": "E36209", "description": ""},
    {"name": "fach:sport", "color": "28A745", "description": ""},
    {"name": "fach:deutsch", "color": "D73A49", "description": ""},
    {"name": "fach:religion", "color": "F9A8D4", "description": ""},
    {"name": "fach:organisation", "color": "959DA5", "description": ""},
]
for sp in (1, 2, 3, 5, 8):
    LABELS.append({"name": f"sp:{sp}", "color": "FBCA04", "description": f"{sp} Story Points"})

EPIC_BY_FACH = {e["fach"]: e["id"] for e in EPICS}


def story_points(start: str, end: str) -> int:
    t0 = datetime.strptime(start, "%H:%M")
    t1 = datetime.strptime(end, "%H:%M")
    minutes = (t1 - t0).seconds // 60
    if minutes <= 45:
        return 1
    if minutes <= 60:
        return 2
    if minutes <= 90:
        return 3
    if minutes <= 150:
        return 5
    return 8


def milestone_for(fach: str, d: date) -> str:
    if d <= date(2027, 1, 10):
        return "M01"
    if fach == "Sport":
        return "M04" if d <= date(2027, 3, 21) else ("M05" if d <= date(2027, 4, 4) else "M06")
    if fach == "Physik":
        if d <= date(2027, 2, 14):
            return "M02"
        if d <= date(2027, 2, 28):
            return "M03"
        if d <= date(2027, 3, 21):
            return "M04"
        return "M05" if d <= date(2027, 4, 4) else "M07"
    if fach == "Mathe":
        if d <= date(2027, 2, 14):
            return "M02"
        if d <= date(2027, 2, 28):
            return "M03"
        if d <= date(2027, 3, 21):
            return "M04"
        return "M05" if d <= date(2027, 4, 4) else "M08"
    if fach in ("Deutsch", "Religion"):
        return "M09" if d <= date(2027, 6, 27) else "M10"
    for m in MILESTONES:
        if d <= date.fromisoformat(m["due"]):
            return m["id"]
    return MILESTONES[-1]["id"]


def build():
    blocks = json.loads((DATA / "lernbloecke.json").read_text(encoding="utf-8"))
    fragen = json.loads((DATA / "testfragen.json").read_text(encoding="utf-8"))
    blocks.sort(key=lambda b: (b["date"], b["start"]))

    # Wochen: Start = Montag des frühesten Blocks, Ende = Sonntag vor dem nächsten Wochenstart
    week_ids = []
    for b in blocks:
        wid = b["week"].split(" ")[0]
        if wid not in week_ids:
            week_ids.append(wid)
    starts = {}
    for b in blocks:
        wid = b["week"].split(" ")[0]
        d = date.fromisoformat(b["date"])
        monday = d - timedelta(days=d.weekday())
        starts[wid] = min(starts.get(wid, monday), monday)
    wochen = []
    for i, wid in enumerate(week_ids):
        start = starts[wid]
        end = (starts[week_ids[i + 1]] - timedelta(days=1)) if i + 1 < len(week_ids) else start + timedelta(days=6)
        label = next(b["week"] for b in blocks if b["week"].startswith(wid + " "))
        wochen.append({"id": wid, "titel": label.split(" ", 1)[1], "start": start.isoformat(), "ende": end.isoformat()})

    stories = []
    for n, b in enumerate(blocks, 1):
        d = date.fromisoformat(b["date"])
        wid = b["week"].split(" ")[0]
        sp = story_points(b["start"], b["end"])
        frage = fragen.get(b["date"])
        stories.append({
            "id": f"US-{n:03d}",
            "epic": EPIC_BY_FACH[b["fach"]],
            "fach": b["fach"],
            "woche": wid,
            "datum": b["date"],
            "wochentag": WOCHENTAGE[d.weekday()],
            "start": b["start"],
            "ende": b["end"],
            "titel": b["thema"],
            "aufgaben": b["aufgaben"],
            "story_points": sp,
            "generalprobe": b.get("kind") == "probe",
            "milestone": milestone_for(b["fach"], d),
            "testfrage": frage["frage"] if frage else None,
            "loesung": frage["loesung"] if frage else None,
        })

    for w in wochen:
        ws = [s for s in stories if s["woche"] == w["id"]]
        w["story_points"] = sum(s["story_points"] for s in ws)
        w["stories"] = [s["id"] for s in ws]
        w["testfragen"] = sum(1 for s in ws if s["testfrage"])

    epics = []
    for e in EPICS:
        es = [s for s in stories if s["epic"] == e["id"]]
        epics.append({**e, "stories": len(es), "story_points": sum(s["story_points"] for s in es)})

    milestones = []
    for m in MILESTONES:
        ms = [s for s in stories if s["milestone"] == m["id"]]
        milestones.append({**m, "stories": len(ms), "story_points": sum(s["story_points"] for s in ms)})

    return stories, epics, milestones, wochen


def write_json(name: str, obj) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def fmt(d: str) -> str:
    return date.fromisoformat(d).strftime("%d.%m.")


def write_docs(stories, epics, milestones, wochen) -> None:
    (DOCS / "wochen").mkdir(parents=True, exist_ok=True)
    total = sum(s["story_points"] for s in stories)

    lines = ["# Abi-Plan 2027 – Übersicht", "", "_Generiert aus `data/` mit `scripts/generate.py`._", "",
             f"**{len(stories)} Lernblöcke · {total} Story Points · {len(wochen)} Wochen · {len(milestones)} Milestones**", "",
             "## Epics", "", "| Epic | Ziel | Blöcke | SP |", "|---|---|---:|---:|"]
    for e in epics:
        lines.append(f"| {e['id']} {e['title']} | {e['ziel']} | {e['stories']} | {e['story_points']} |")
    lines += ["", "## Wochen", "", "| Woche | Zeitraum | Blöcke | SP | Testfragen |", "|---|---|---:|---:|---:|"]
    for w in wochen:
        lines.append(f"| [{w['id']}](wochen/{w['id']}.md) {w['titel']} | {fmt(w['start'])}–{fmt(w['ende'])} | {len(w['stories'])} | {w['story_points']} | {w['testfragen']} |")
    (DOCS / "plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = ["# Milestones", "", "_Generiert._", "", "| Milestone | Fällig | Blöcke | SP | Beschreibung |", "|---|---|---:|---:|---|"]
    for m in milestones:
        lines.append(f"| {m['id']} {m['title']} | {fmt(m['due'])} | {m['stories']} | {m['story_points']} | {m['beschreibung']} |")
    (DOCS / "milestones.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for w in wochen:
        ws = [s for s in stories if s["woche"] == w["id"]]
        lines = [f"# {w['id']} · {w['titel']}", "", f"{fmt(w['start'])}–{fmt(w['ende'])} · {w['story_points']} Story Points", ""]
        for s in ws:
            tag = " · Generalprobe" if s["generalprobe"] else ""
            lines += [f"## {s['id']} · {s['wochentag']} {fmt(s['datum'])} {s['start']}–{s['ende']} · {s['fach']} · {s['story_points']} SP{tag}",
                      f"**{s['titel']}**", ""]
            lines += [f"- [ ] {a}" for a in s["aufgaben"]]
            if s["testfrage"]:
                lines += ["", f"Testfrage: {s['testfrage']}"]
            lines.append("")
        (DOCS / "wochen" / f"{w['id']}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    stories, epics, milestones, wochen = build()
    write_json("stories.json", stories)
    write_json("epics.json", epics)
    write_json("milestones.json", milestones)
    write_json("wochen.json", wochen)
    write_json("labels.json", LABELS + [{"name": f"woche:{w['id']}", "color": "C5DEF5", "description": f"{fmt(w['start'])}–{fmt(w['ende'])}"} for w in wochen])
    write_docs(stories, epics, milestones, wochen)
    print(f"{len(stories)} Stories, {len(wochen)} Wochen, {sum(s['story_points'] for s in stories)} SP")


if __name__ == "__main__":
    main()
