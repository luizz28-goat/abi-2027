#!/usr/bin/env python3
"""Kanonischer Generator für den Abi-Plan.

Eingaben (von Hand gepflegt):
  data/lernbloecke.json  – alle Lernblöcke (Datum, Zeit, Fach, Thema, Aufgaben, Woche, Art; optional
                           phase, ziel, claude, material, infos)
  data/testfragen.json   – eine Testfrage pro Lernblock (Schlüssel = "YYYY-MM-DD HH:MM" oder Datum)

Ausgaben (generiert, nicht von Hand ändern):
  data/stories.json, data/epics.json, data/milestones.json, data/wochen.json, data/labels.json,
  data/kalender.json (Titel + Beschreibung jedes Kalendertermins)
  docs/plan.md, docs/milestones.md, docs/wochen/Wxx.md, docs/wochen/Kxx.md

Zwei Phasen:
  klausuren – Klausuren 1. Halbjahr Jg12 (Okt–Dez 2026), Stories KL-001 …, Wochen K01 …
  abi       – Abiturvorbereitung (Jan–Jun 2027), Stories US-001 …, Wochen W01 …

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
    {"id": "E07", "fach": "Klausuren", "label": "phase:klausuren", "title": "Klausuren 1. Halbjahr Jg12 (Okt–Dez 2026)", "ziel": "In allen Klausuren bis 21.12.2026 auf 13–15 Punkte: jeder Block erledigt, vor Mathe, Physik, Englisch und Deutsch eine Probeklausur."},
]

# Klausuren 1. Halbjahr Jg12 (Klausurplan Stand 29.09.2026; Sport-Klausur 16.10. gibt es nicht)
KLAUSUREN = [
    ("2026-11-09", "Mathe", "Mathe-LK (M1, Frau Assem)"),
    ("2026-11-12", "Physik", "Physik-LK (PH1, Herr Baier)"),
    ("2026-11-17", "Kunst", "Kunst (bk2, Herr Kunze)"),
    ("2026-11-23", "Geschichte", "Geschichte (g3, Frau Schubert)"),
    ("2026-11-26", "Englisch", "Englisch (e1, Frau Buchalla)"),
    ("2026-12-03", "Deutsch", "Deutsch (d1, Frau Keller, 3.–6. Std.)"),
    ("2026-12-07", "Gemeinschaftskunde", "Gemeinschaftskunde (gk, Su)"),
    ("2026-12-11", "Sport", "Sport-LK (Sp1, Herr Werner, im Plan als KOOP)"),
    ("2026-12-14", "Religion", "Religion (rev1, Herr Keller)"),
    ("2026-12-17", "Physik", "Physik-LK (PH1, Herr Baier)"),
    ("2026-12-21", "Mathe", "Mathe-LK (M1, Frau Assem)"),
]

MILESTONES_KLAUSUREN = [
    {"id": f"K{n:02d}", "title": f"Klausur {fach} {date.fromisoformat(d):%d.%m.}", "due": d, "fach": fach,
     "beschreibung": f"Klausur {name}. Alle Blöcke davor erledigt, Probeklausur bzw. letzter Check gemacht."}
    for n, (d, fach, name) in enumerate(KLAUSUREN, 1)
]

MILESTONES = MILESTONES_KLAUSUREN + [
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
    {"name": "fach:kunst", "color": "C2E0C6", "description": ""},
    {"name": "fach:geschichte", "color": "D4C5F9", "description": ""},
    {"name": "fach:englisch", "color": "0075CA", "description": ""},
    {"name": "fach:gemeinschaftskunde", "color": "FEF2C0", "description": ""},
    {"name": "phase:klausuren", "color": "5319E7", "description": "Klausuren 1. Halbjahr (Okt–Dez 2026)"},
    {"name": "phase:abi", "color": "0E8A16", "description": "Abiturvorbereitung (Jan–Jun 2027)"},
]
for sp in (1, 2, 3, 5, 8):
    LABELS.append({"name": f"sp:{sp}", "color": "FBCA04", "description": f"{sp} Story Points"})

EPIC_BY_FACH = {e["fach"]: e["id"] for e in EPICS if e["id"] != "E07"}
PRUEFUNGEN_ABI = {"Sport": "2027-04-19", "Physik": "2027-04-20", "Mathe": "2027-05-05",
                  "Deutsch": "2027-06-28", "Religion": "2027-06-28", "Organisation": "2027-06-30"}
REPO_URL = "https://github.com/luizz28-goat/abi-2027"

# ---------------------------------------------------------------------------
# Briefing pro Block: was Luiz tut, was Claude bei „bearbeite diesen Termin“ tut
# ---------------------------------------------------------------------------
NOTION = "Notion: „Schule – Lernversionen“"
MATERIAL = {
    "Mathe": ["Mathebattle (Kurs M1 LF von Frau Assem) – im Browser der Claude-App angemeldet",
              "BW-Abi Leistungsfach 2019–2026 mit Lösungen: mathe-aufgaben.com → Prüfungsaufgaben → Abitur → Allg. Gymnasien → Leistungsfach",
              f"{NOTION} → Mathe, Fehlerliste Mathe"],
    "Physik": ["LEIFI Physik (leifiphysik.de): Erklärungen + Aufgaben mit Lösung",
               "BW-Abi Physik (IBBW-Prüfungen, Stark-Heft falls vorhanden)",
               f"{NOTION} → Physik, Formelsammlung, Fehlerliste Physik"],
    "Sport": [f"{NOTION} → Sport", "Stark Abiturprüfung BW Sport / Material von Herrn Werner"],
    "Deutsch": ["Lektüre (Woyzeck, Mario und der Zauberer) mit Szenen-/Seitenangaben", f"{NOTION} → Deutsch", "Operatorenliste Deutsch BW"],
    "Religion": [f"{NOTION} → Religion", "Bibel (Stellenangaben aus dem Unterricht)", "Operatorenliste Religion BW"],
    "Kunst": [f"{NOTION} → Kunst", "Werkabbildungen (Claude sucht passende Bilder mit Link raus)"],
    "Geschichte": [f"{NOTION} → Geschichte", "Operatorenliste Geschichte BW", "Quellen aus dem Unterricht"],
    "Englisch": [f"{NOTION} → Englisch (Vokabeln, Redemittel)", "Texte aus dem Unterricht"],
    "Gemeinschaftskunde": [f"{NOTION} → Gemeinschaftskunde", "Operatorenliste Gemeinschaftskunde BW"],
    "Organisation": ["Google Drive: GoodNotes-Backup und Ordner Schule/Memo (Sprachmemos)", NOTION],
}
CLAUDE_STANDARD = {
    "probe": ["Die Prüfung aus den Aufgaben bereitstellen (Link/PDF), Zeit und erlaubte Hilfsmittel nennen",
              "Nach der Abgabe (Foto/Scan) mit Erwartungshorizont korrigieren und Punkte angeben",
              "Fehler in die Fehlerliste übernehmen und die nächsten Blöcke darauf ausrichten"],
    "block": ["Die in den Aufgaben genannten Aufgaben/Quellen raussuchen: Jahrgang, Aufgabennummer, Link, Zeitvorgabe",
              "Lernversionen zum Thema in Notion lesen und eine Kurz-Erklärung der Kernidee vorbereiten",
              "Aufgabenblatt vorlegen, Lösungen erst nach Luiz' Abgabe zeigen, korrigieren, Fehler in die Fehlerliste"],
}
CLAUDE_ABSCHLUSS = "Zum Schluss: Issue abhaken und schließen, neue Infos in Lernplan-Status, Repo und Kalender nachtragen"


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


def klausur_fuer(fach: str, d: date):
    """Nächste Klausur dieses Fachs am oder nach d (Organisation: nächste Klausur überhaupt)."""
    for m in MILESTONES_KLAUSUREN:
        if date.fromisoformat(m["due"]) > d and (fach == "Organisation" or m["fach"] == fach):
            return m
    return None


def milestone_for(fach: str, d: date, phase: str = "abi") -> str:
    if phase == "klausuren":
        return klausur_fuer(fach, d)["id"]
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
    phase_of = {b["week"].split(" ")[0]: b.get("phase", "abi") for b in blocks}
    last = {}
    for b in blocks:
        wid = b["week"].split(" ")[0]
        last[wid] = max(last.get(wid, b["date"]), b["date"])
    wochen = []
    for i, wid in enumerate(week_ids):
        start = starts[wid]
        if i + 1 < len(week_ids):
            end = starts[week_ids[i + 1]] - timedelta(days=1)
            if phase_of[week_ids[i + 1]] != phase_of[wid]:
                # Phasenwechsel (z. B. Weihnachtsferien): Woche endet am Sonntag nach dem letzten Block
                ld = date.fromisoformat(last[wid])
                end = min(end, ld + timedelta(days=6 - ld.weekday()))
        else:
            end = start + timedelta(days=6)
        label = next(b["week"] for b in blocks if b["week"].startswith(wid + " "))
        wochen.append({"id": wid, "titel": label.split(" ", 1)[1], "start": start.isoformat(), "ende": end.isoformat(),
                       "phase": phase_of[wid]})

    stories = []
    zaehler = {"klausuren": 0, "abi": 0}
    for b in blocks:
        d = date.fromisoformat(b["date"])
        wid = b["week"].split(" ")[0]
        phase = b.get("phase", "abi")
        zaehler[phase] += 1
        sid = f"{'KL' if phase == 'klausuren' else 'US'}-{zaehler[phase]:03d}"
        sp = story_points(b["start"], b["end"])
        frage = fragen.get(f"{b['date']} {b['start']}") or (None if phase == "klausuren" else fragen.get(b["date"]))
        if phase == "klausuren":
            k = klausur_fuer(b["fach"], d)
            name = next(n for kd, kf, n in KLAUSUREN if kd == k["due"] and kf == k["fach"])
            pruefung = k["due"]
            pruefung_name = ("nächste Klausur: " if b["fach"] == "Organisation" else "Klausur ") + name
        else:
            pruefung = PRUEFUNGEN_ABI[b["fach"]]
            pruefung_name = next(e["title"] for e in EPICS if e["id"] == EPIC_BY_FACH[b["fach"]])
        kind = b.get("kind", "block")
        stories.append({
            "id": sid,
            "phase": phase,
            "epic": "E07" if phase == "klausuren" else EPIC_BY_FACH[b["fach"]],
            "fach": b["fach"],
            "woche": wid,
            "datum": b["date"],
            "wochentag": WOCHENTAGE[d.weekday()],
            "start": b["start"],
            "ende": b["end"],
            "titel": b["thema"],
            "aufgaben": b["aufgaben"],
            "story_points": sp,
            "generalprobe": kind == "probe",
            "milestone": milestone_for(b["fach"], d, phase),
            "pruefung": pruefung,
            "pruefung_name": pruefung_name,
            "testfrage": frage["frage"] if frage else None,
            "loesung": frage["loesung"] if frage else None,
            "briefing": {
                "ziel": b.get("ziel") or b["thema"],
                "claude": (b.get("claude") or CLAUDE_STANDARD["probe" if kind == "probe" else "block"]) + [CLAUDE_ABSCHLUSS],
                "material": b.get("material") or MATERIAL.get(b["fach"], [NOTION]),
                "infos": b.get("infos", []),
            },
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
    lines += ["", "## Klausuren 1. Halbjahr", "", "| Datum | Klausur | Blöcke | SP |", "|---|---|---:|---:|"]
    for m in milestones:
        if m["id"].startswith("K"):
            lines.append(f"| {fmt(m['due'])} | {m['title']} | {m['stories']} | {m['story_points']} |")
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
            br = s["briefing"]
            lines += [f"Ziel: {br['ziel']}", "", "Aufgaben:", ""]
            lines += [f"- [ ] {a}" for a in s["aufgaben"]]
            lines += ["", "Claude bei „bearbeite diesen Termin“:", ""]
            lines += [f"{n}. {c}" for n, c in enumerate(br["claude"], 1)]
            if br["infos"]:
                lines += ["", "Braucht Claude von Luiz: " + " · ".join(br["infos"])]
            if s["testfrage"]:
                lines += ["", f"Testfrage: {s['testfrage']}"]
            lines.append("")
        (DOCS / "wochen" / f"{w['id']}.md").write_text("\n".join(lines), encoding="utf-8")


WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def kalender(s: dict) -> dict:
    """Titel und Beschreibung des Kalendertermins – so vollständig, dass „bearbeite diesen Termin“ reicht."""
    br = s["briefing"]
    d = date.fromisoformat(s["datum"])
    p = date.fromisoformat(s["pruefung"])
    if s["titel"].startswith("Letzter Check"):
        emoji = "✅"
    elif s["generalprobe"]:
        emoji = "📝"
    elif s["fach"] == "Organisation":
        emoji = "🗂️"
    else:
        emoji = "📚"
    if s["phase"] == "klausuren":
        summary = f"{emoji} {s['fach']} · {s['titel']}" if s["fach"] != "Organisation" else f"{emoji} {s['titel']}"
        fuer = f"{s['pruefung_name']} am {WT[p.weekday()]} {p:%d.%m.} – noch {(p - d).days} Tag{'' if (p - d).days == 1 else 'e'}"
    else:
        summary = f"Abi-{'Generalprobe' if s['generalprobe'] else 'Lernblock'} {s['fach']}: {s['titel']}"
        fuer = f"{s['pruefung_name']} – noch {(p - d).days} Tag{'' if (p - d).days == 1 else 'e'}"
    issue = f"{REPO_URL}/issues?q=is%3Aissue+{s['id']}"
    zeilen = [f"🎯 Ziel: {br['ziel']}",
              f"📌 Für: {fuer}",
              f"⏱ {s['start']}–{s['ende']} · {s['story_points']} Story Points · {s['id']} · Woche {s['woche']}",
              "", "✅ DEINE AUFGABEN"]
    zeilen += [f"☐ {a}" for a in s["aufgaben"]]
    zeilen += ["", "🤖 „BEARBEITE DIESEN TERMIN“ – DAS MACHT CLAUDE"]
    zeilen += [f"{n}. {c}" for n, c in enumerate(br["claude"], 1)]
    zeilen += ["", "📚 MATERIAL"] + [f"• {m}" for m in br["material"]]
    if br["infos"]:
        zeilen += ["", "❓ BRAUCHT CLAUDE VON DIR (falls noch nicht im Lernplan-Status)"] + [f"• {i}" for i in br["infos"]]
    erledigt = f"🏁 ERLEDIGT: Aufgaben gemacht · Issue {s['id']} geschlossen"
    if s["testfrage"]:
        erledigt += f" · Testfrage im Wochentest {s['woche']} richtig"
    zeilen += ["", erledigt, f"Issue: {issue}"]
    return {"id": s["id"], "datum": s["datum"], "start": s["start"], "ende": s["ende"],
            "summary": summary, "colorId": "3" if s["generalprobe"] and s["phase"] == "abi" else "9",
            "description": "\n".join(zeilen)}


def main() -> None:
    stories, epics, milestones, wochen = build()
    write_json("kalender.json", [kalender(s) for s in stories])
    write_json("stories.json", stories)
    write_json("epics.json", epics)
    write_json("milestones.json", milestones)
    write_json("wochen.json", wochen)
    write_json("labels.json", LABELS + [{"name": f"woche:{w['id']}", "color": "C5DEF5", "description": f"{fmt(w['start'])}–{fmt(w['ende'])}"} for w in wochen])
    write_docs(stories, epics, milestones, wochen)
    print(f"{len(stories)} Stories, {len(wochen)} Wochen, {sum(s['story_points'] for s in stories)} SP")


if __name__ == "__main__":
    main()
