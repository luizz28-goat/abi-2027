#!/usr/bin/env python3
"""Legt Labels, Milestones, Epic-Issues, Lernblock-Issues und das Fortschritts-Issue an.

Idempotent: jedes Issue trägt einen versteckten Marker (<!-- abi-story: US-001 -->).
Ein zweiter Lauf legt nichts doppelt an, sondern ergänzt nur Fehlendes und
aktualisiert Texte von Lernblöcken, die noch offen sind.

Läuft automatisch über .github/workflows/bootstrap.yml nach jedem Push auf main.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_api import GitHub, find_marker, marker  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def fmt(d: str) -> str:
    return date.fromisoformat(d).strftime("%d.%m.%Y")


def story_body(s: dict, epic_numbers: dict) -> str:
    epic = epic_numbers.get(s["epic"])
    lines = [
        marker("story", s["id"]),
        f"**{s['wochentag']} {fmt(s['datum'])} · {s['start']}–{s['ende']}** · {s['fach']} · **{s['story_points']} Story Points**"
        + (" · Generalprobe" if s["generalprobe"] else ""),
        "",
        f"Woche: `{s['woche']}` · Milestone: `{s['milestone']}` · Epic: " + (f"#{epic}" if epic else s["epic"]),
        "",
        "## Aufgaben",
        "",
        *[f"- [ ] {a}" for a in s["aufgaben"]],
        "",
        "## Erledigt, wenn",
        "",
        "- alle Aufgaben abgehakt sind,",
        "- das Issue geschlossen ist (Close → „completed“),",
        "- und die Testfrage im Wochentest am Sonntag richtig beantwortet wurde." if s["testfrage"] else "",
        "",
        "Nicht geschafft? Einfach offen lassen – der Wochenabschluss am Sonntag schiebt den Block automatisch mit Label `nachholen` in die nächste Woche.",
    ]
    return "\n".join(lines)


def main() -> None:
    gh = GitHub()
    stories = load("stories.json")
    epics = load("epics.json")
    milestones = load("milestones.json")
    labels = load("labels.json")

    # Labels
    existing = {l["name"]: l for l in gh.get_all(gh.r("/labels"))}
    for l in labels:
        if l["name"] in existing:
            continue
        gh.request("POST", gh.r("/labels"), l)
        print("Label", l["name"])

    # Milestones
    ms_existing = {m["title"]: m for m in gh.get_all(gh.r("/milestones?state=all"))}
    ms_numbers = {}
    for m in milestones:
        title = f"{m['id']} {m['title']}"
        payload = {"title": title, "description": m["beschreibung"], "due_on": f"{m['due']}T20:00:00Z"}
        if title in ms_existing:
            ms_numbers[m["id"]] = ms_existing[title]["number"]
        else:
            created = gh.request("POST", gh.r("/milestones"), payload)[0]
            ms_numbers[m["id"]] = created["number"]
            print("Milestone", title)

    issues = gh.issues()
    by_marker = {}
    for i in issues:
        for kind in ("story", "epic", "fortschritt"):
            v = find_marker(i.get("body"), kind)
            if v:
                by_marker[(kind, v)] = i

    # Epics
    epic_numbers = {}
    for e in epics:
        key = ("epic", e["id"])
        children = [s for s in stories if s["epic"] == e["id"]]
        body = "\n".join([marker("epic", e["id"]), f"**Ziel:** {e['ziel']}", "",
                          f"{e['stories']} Lernblöcke · {e['story_points']} Story Points", "",
                          "Fortschritt: siehe Lernblöcke mit diesem Epic und das Fortschritts-Issue."])
        if key in by_marker:
            epic_numbers[e["id"]] = by_marker[key]["number"]
        else:
            created = gh.create_issue(f"[{e['id']}] {e['title']}", body, ["type:epic", f"fach:{e['fach'].lower()}"])
            epic_numbers[e["id"]] = created["number"]
            print("Epic", e["id"])

    # Lernblöcke
    for s in stories:
        key = ("story", s["id"])
        title = f"[{s['woche']}] {s['fach']}: {s['titel']}"
        body = story_body(s, epic_numbers)
        if key in by_marker:
            issue = by_marker[key]
            # Nur Text auffrischen, solange der Block offen ist; Labels (Woche/nachholen) gehören dem Wochenabschluss.
            if issue["state"] == "open" and issue["body"] != body:
                gh.update_issue(issue["number"], body=body)
            continue
        lab = ["type:lernblock", f"fach:{s['fach'].lower()}", f"woche:{s['woche']}", f"sp:{s['story_points']}"]
        if s["generalprobe"]:
            lab.append("generalprobe")
        gh.create_issue(title, body, lab, ms_numbers[s["milestone"]])
        print("Story", s["id"])

    # Fortschritts-Issue
    if ("fortschritt", "main") not in by_marker:
        created = gh.create_issue("📊 Fortschritt Abi 2027", marker("fortschritt", "main") + "\n\nWird jeden Sonntag vom Wochenabschluss aktualisiert.", ["type:fortschritt"])
        print("Fortschritt", created["number"])

    print("Bootstrap fertig.")


if __name__ == "__main__":
    main()
