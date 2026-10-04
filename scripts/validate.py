#!/usr/bin/env python3
"""Prüft, ob die Plandaten in sich stimmig sind. Bricht mit Fehlermeldung ab, wenn nicht."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRUEFUNGEN = {"Sport": date(2027, 4, 19), "Physik": date(2027, 4, 20), "Mathe": date(2027, 5, 5),
              "Deutsch": date(2027, 6, 28), "Religion": date(2027, 6, 28)}


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def main() -> int:
    fehler = []
    stories, wochen, ms, epics = load("stories.json"), load("wochen.json"), load("milestones.json"), load("epics.json")
    ids = [s["id"] for s in stories]
    if len(ids) != len(set(ids)):
        fehler.append("Doppelte Story-IDs")
    ms_ids = {m["id"] for m in ms}
    epic_ids = {e["id"] for e in epics}
    week_ids = {w["id"] for w in wochen}
    slots = set()
    for s in stories:
        d = date.fromisoformat(s["datum"])
        if s["milestone"] not in ms_ids:
            fehler.append(f"{s['id']}: unbekannter Milestone {s['milestone']}")
        if s["epic"] not in epic_ids:
            fehler.append(f"{s['id']}: unbekanntes Epic {s['epic']}")
        if s["woche"] not in week_ids:
            fehler.append(f"{s['id']}: unbekannte Woche {s['woche']}")
        if not s["aufgaben"]:
            fehler.append(f"{s['id']}: keine Aufgaben")
        if s["story_points"] not in (1, 2, 3, 5, 8):
            fehler.append(f"{s['id']}: Story Points {s['story_points']} nicht in Fibonacci-Reihe")
        p = PRUEFUNGEN.get(s["fach"])
        if p and d > p:
            fehler.append(f"{s['id']}: Lernblock {s['fach']} nach der Prüfung ({d})")
        for fach, pd in PRUEFUNGEN.items():
            if d == pd and s["start"] < "15:00" and s["fach"] != "Organisation":
                fehler.append(f"{s['id']}: Lernblock am Prüfungstag {fach} vormittags")
        key = (s["datum"], s["start"])
        if key in slots:
            fehler.append(f"{s['id']}: zwei Blöcke zur selben Zeit {key}")
        slots.add(key)
        if s["fach"] in ("Mathe", "Physik", "Sport", "Deutsch", "Religion") and not s["titel"].startswith("Letzter Check") and not s["testfrage"]:
            fehler.append(f"{s['id']}: keine Testfrage")
    for a, b in zip(wochen, wochen[1:]):
        if date.fromisoformat(a["ende"]) >= date.fromisoformat(b["start"]):
            fehler.append(f"Wochen {a['id']}/{b['id']} überlappen")
    for m in ms:
        if m["stories"] == 0:
            fehler.append(f"Milestone {m['id']} hat keine Stories")
    if fehler:
        print("\n".join("✗ " + f for f in fehler))
        return 1
    print(f"✓ {len(stories)} Stories, {len(wochen)} Wochen, {len(ms)} Milestones – alles stimmig")
    return 0


if __name__ == "__main__":
    sys.exit(main())
