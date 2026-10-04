#!/usr/bin/env python3
"""Wochenstart und Wochenabschluss.

  python3 scripts/woche.py start      [--woche W05] [--heute 2027-02-01]
  python3 scripts/woche.py abschluss  [--woche W05] [--heute 2027-02-07]

start (Montag früh):
  Legt das Issue „Wochentest Wxx“ an. Es enthält eine Testfrage zu jedem Lernblock,
  der in dieser Woche das Label woche:Wxx trägt – also auch zu nachgeholten Blöcken.

abschluss (Sonntagabend, nach dem Wochencheck):
  1. Liest im Wochentest, welche Fragen als richtig abgehakt sind.
  2. Jeder Block der Woche, der noch offen ist ODER dessen Testfrage nicht abgehakt ist,
     wird (wieder) geöffnet, bekommt das Label `nachholen` und wandert in die nächste Woche.
  3. Gibt es Nachhol-Blöcke, entsteht in der nächsten Woche ein Issue „Nachholblock“ mit
     Story Points und Terminvorschlägen – die nächste Woche wird also länger.
  4. Schließt den Wochentest mit Ergebnis-Kommentar und aktualisiert das Fortschritts-Issue.

Ohne --woche wird die Woche aus dem heutigen Datum (Europe/Berlin) bestimmt.
Läuft automatisch über .github/workflows/woche.yml.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_api import find_marker, marker  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BESTANDEN = 0.8  # Anteil richtiger Testfragen, ab dem eine Woche als bestanden gilt
NACHHOL_SLOTS = "Fr 09:45–11:00 (Freistunde) und So 16:00–17:30 – oder einen Block vor den Wochencheck legen"
PRUEFUNGEN = {"Sport": date(2027, 4, 19), "Physik": date(2027, 4, 20), "Mathe": date(2027, 5, 5),
              "Deutsch": date(2027, 6, 28), "Religion": date(2027, 6, 28)}
CHECK_RE = re.compile(r"^- \[([ xX])\] F\d+ · ((?:US|KL)-\d{3})", re.M)


def pruefung(s: dict) -> date:
    """Klausur bzw. Abiprüfung, für die der Block lernt. Danach wird er nicht mehr verschoben."""
    if s.get("pruefung"):
        return date.fromisoformat(s["pruefung"])
    return PRUEFUNGEN.get(s["fach"], date.max)


def load(name: str):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def heute_berlin() -> date:
    # Mitteleuropäische Zeit ohne externe Bibliothek: Sommerzeit grob über letzten Sonntag im März/Oktober.
    now = datetime.now(timezone.utc)
    year = now.year
    def last_sunday(month: int) -> datetime:
        d = datetime(year, month, 31, 1, tzinfo=timezone.utc)
        return d - timedelta(days=(d.weekday() + 1) % 7)
    offset = 2 if last_sunday(3) <= now < last_sunday(10) else 1
    return (now + timedelta(hours=offset)).date()


def label_names(issue: dict) -> set[str]:
    return {l["name"] if isinstance(l, dict) else l for l in issue.get("labels", [])}


def woche_fuer(wochen: list, heute: date, art: str):
    for i, w in enumerate(wochen):
        if art == "start" and date.fromisoformat(w["start"]) == heute:
            return i
        if art == "abschluss" and date.fromisoformat(w["ende"]) == heute:
            return i
    return None


def story_issues(gh, woche_id: str) -> dict:
    result = {}
    for i in gh.issues(labels=f"woche:{woche_id}"):
        sid = find_marker(i.get("body"), "story")
        if sid:
            result[sid] = i
    return result


def start(gh, wochen, stories, idx: int) -> None:
    w = wochen[idx]
    for i in gh.issues(labels="type:wochentest"):
        if find_marker(i.get("body"), "test") == w["id"]:
            print(f"Wochentest {w['id']} existiert schon (#{i['number']}).")
            return
    by_id = {s["id"]: s for s in stories}
    issues = story_issues(gh, w["id"])
    fragen = [(sid, issue) for sid, issue in sorted(issues.items()) if by_id.get(sid, {}).get("testfrage")]
    lines = [marker("test", w["id"]),
             f"Wochentest **{w['id']}** ({date.fromisoformat(w['start']):%d.%m.}–{date.fromisoformat(w['ende']):%d.%m.}).",
             "",
             "**So geht's (Sonntag beim Wochencheck, 18:00):**",
             "1. Alle Fragen **ohne Unterlagen** beantworten – auf Papier oder als Nachricht an Claude.",
             "2. Erst dann die Lösungen aufklappen und vergleichen (oder Claude korrigieren lassen).",
             "3. **Nur richtig beantwortete Fragen abhaken.** Selbstauskünfte nur abhaken, wenn sie wirklich stimmen.",
             f"4. Um 20 Uhr läuft der Wochenabschluss: nicht abgehakte Fragen und offene Blöcke werden in die nächste Woche geschoben. Bestanden ab {int(BESTANDEN*100)} %.",
             "", "## Fragen", ""]
    for n, (sid, issue) in enumerate(fragen, 1):
        s = by_id[sid]
        nach = " · 🔁 nachgeholt" if "nachholen" in label_names(issue) else ""
        lines.append(f"- [ ] F{n} · {sid} · {s['fach']} (#{issue['number']}){nach}: {s['testfrage']}")
    lines += ["", "<details><summary>Lösungen (erst nach dem Beantworten öffnen)</summary>", ""]
    for n, (sid, _) in enumerate(fragen, 1):
        lines.append(f"- F{n}: {by_id[sid]['loesung']}")
    lines += ["", "</details>"]
    if not fragen:
        lines += ["_Diese Woche gibt es keine Testfragen._"]
    if w.get("phase") == "klausuren":
        lines.insert(2, "_Klausurphase 1. Halbjahr: Fragen zu Blöcken ohne festes Thema beantwortest du am besten als Nachricht an Claude, der prüft gegen deine Lernversionen._\n")
    created = gh.create_issue(f"[Wochentest {w['id']}] {w['titel']}", "\n".join(lines), ["type:wochentest", f"woche:{w['id']}"])
    print(f"Wochentest {w['id']} angelegt (#{created['number']}), {len(fragen)} Fragen.")


def abschluss(gh, wochen, stories, idx: int) -> None:
    w = wochen[idx]
    naechste = wochen[idx + 1] if idx + 1 < len(wochen) else None
    by_id = {s["id"]: s for s in stories}
    ende = date.fromisoformat(w["ende"])

    test = next((i for i in gh.issues(labels="type:wochentest") if find_marker(i.get("body"), "test") == w["id"]), None)
    richtig, gefragt = set(), set()
    if test:
        for mark, sid in CHECK_RE.findall(test.get("body") or ""):
            gefragt.add(sid)
            if mark.lower() == "x":
                richtig.add(sid)

    issues = story_issues(gh, w["id"])
    nachholen, erledigt = [], []
    for sid, issue in sorted(issues.items()):
        s = by_id.get(sid)
        if not s or date.fromisoformat(s["datum"]) > ende and "nachholen" not in label_names(issue):
            continue  # Termin liegt nach dem Wochenende (z. B. Prüfungstag) – bleibt stehen
        offen = issue["state"] == "open"
        test_falsch = sid in gefragt and sid not in richtig
        if offen or test_falsch:
            grund = "nicht erledigt" if offen else "Testfrage nicht richtig beantwortet"
            nachholen.append((sid, issue, grund))
        else:
            erledigt.append((sid, issue))

    # Nach der Prüfung eines Fachs wird nichts mehr verschoben
    if naechste:
        nstart = date.fromisoformat(naechste["start"])
        vorbei = [(sid, i, g) for sid, i, g in nachholen if pruefung(by_id[sid]) <= nstart]
        for sid, issue, _ in vorbei:
            gh.comment(issue["number"], f"{by_id[sid].get('pruefung_name', 'Prüfung')} ist vorbei – Block wird nicht mehr verschoben.")
            gh.update_issue(issue["number"], state="closed", state_reason="not_planned")
        nachholen = [x for x in nachholen if x not in vorbei]

    if naechste:
        for sid, issue, grund in nachholen:
            labels = [l for l in label_names(issue) if not l.startswith("woche:")] + [f"woche:{naechste['id']}", "nachholen"]
            gh.update_issue(issue["number"], state="open", labels=sorted(set(labels)))
            gh.comment(issue["number"], f"⏩ In **{naechste['id']}** verschoben ({grund}). Bitte nachholen und danach wieder schließen.")
        # Bereits erledigte Nachhol-Blöcke verlieren das Label
        for sid, issue in erledigt:
            if "nachholen" in label_names(issue):
                gh.update_issue(issue["number"], labels=sorted(label_names(issue) - {"nachholen"}))

    sp_nach = sum(by_id[sid]["story_points"] for sid, _, _ in nachholen)
    quote = (len(richtig) / len(gefragt)) if gefragt else None
    bestanden = quote is None or quote >= BESTANDEN

    if naechste and nachholen:
        liste = "\n".join(f"- [ ] #{i['number']} {by_id[sid]['fach']}: {by_id[sid]['titel']} ({by_id[sid]['story_points']} SP) – {g}" for sid, i, g in nachholen)
        body = "\n".join([marker("nachhol", naechste["id"]),
                          f"Aus **{w['id']}** sind **{len(nachholen)} Blöcke / {sp_nach} Story Points** offen. Diese Woche wird deshalb länger:",
                          f"geplant {naechste['story_points']} SP + {sp_nach} SP Nachholen = **{naechste['story_points'] + sp_nach} SP**.", "",
                          f"Vorschlag für die Zusatzzeit: {NACHHOL_SLOTS}.", "", liste, "",
                          "Die Blöcke kommen im nächsten Wochentest erneut dran."])
        gh.create_issue(f"[{naechste['id']}] Nachholblock aus {w['id']} ({sp_nach} SP)", body, ["nachholen", f"woche:{naechste['id']}", "fach:organisation"])

    if test:
        q = f"{len(richtig)}/{len(gefragt)} richtig ({quote:.0%})" if gefragt else "keine Fragen"
        status = "✅ bestanden" if bestanden else "❌ nicht bestanden"
        txt = [f"**Ergebnis {w['id']}: {q} – {status}**", "",
               f"Erledigt: {len(erledigt)} Blöcke · Nachholen: {len(nachholen)} Blöcke ({sp_nach} SP)"]
        if nachholen and naechste:
            txt.append(f"Die offenen Blöcke stehen jetzt in **{naechste['id']}** mit Label `nachholen`.")
        gh.comment(test["number"], "\n".join(txt))
        gh.update_issue(test["number"], state="closed", state_reason="completed" if bestanden else "not_planned")

    fortschritt(gh, wochen, stories, w["id"], quote, len(erledigt), len(nachholen), sp_nach)
    print(f"Abschluss {w['id']}: richtig {len(richtig)}/{len(gefragt)}, nachholen {len(nachholen)} ({sp_nach} SP)")


def fortschritt(gh, wochen, stories, woche_id, quote, n_erledigt, n_nach, sp_nach) -> None:
    issue = next((i for i in gh.issues(labels="type:fortschritt") if find_marker(i.get("body"), "fortschritt") == "main"), None)
    if not issue:
        return
    body = issue.get("body") or ""
    verlauf = []
    if "<!-- verlauf:" in body:
        verlauf = json.loads(body.split("<!-- verlauf:", 1)[1].split("-->", 1)[0])
    verlauf = [v for v in verlauf if v["woche"] != woche_id]
    verlauf.append({"woche": woche_id, "quote": quote, "erledigt": n_erledigt, "nachholen": n_nach, "sp_nach": sp_nach})
    verlauf.sort(key=lambda v: v["woche"])

    by_id = {s["id"]: s for s in stories}
    alle = gh.issues(labels="type:lernblock")
    sp_gesamt = sum(s["story_points"] for s in stories)
    sp_fertig = 0
    pro_ms = {}
    for i in alle:
        sid = find_marker(i.get("body"), "story")
        if not sid or sid not in by_id:
            continue
        s = by_id[sid]
        m = pro_ms.setdefault(s["milestone"], [0, 0])
        m[1] += s["story_points"]
        if i["state"] == "closed":
            sp_fertig += s["story_points"]
            m[0] += s["story_points"]
    ms_titel = {m["id"]: m for m in load("milestones.json")}
    balken = lambda a, b: ("█" * round(10 * a / b) + "░" * (10 - round(10 * a / b))) if b else "░" * 10

    lines = [marker("fortschritt", "main"), f"_Stand: Abschluss {woche_id}_", "",
             f"## Gesamt: {sp_fertig}/{sp_gesamt} Story Points {balken(sp_fertig, sp_gesamt)} {sp_fertig/sp_gesamt:.0%}", "",
             "## Milestones", "", "| Milestone | fällig | SP | |", "|---|---|---:|---|"]
    for mid, (a, b) in sorted(pro_ms.items()):
        m = ms_titel[mid]
        lines.append(f"| {mid} {m['title']} | {date.fromisoformat(m['due']):%d.%m.} | {a}/{b} | {balken(a, b)} |")
    lines += ["", "## Wochentests", "", "| Woche | Test | erledigt | nachgeholt (SP) |", "|---|---:|---:|---:|"]
    for v in verlauf:
        q = "–" if v["quote"] is None else f"{v['quote']:.0%}" + (" ✅" if v["quote"] >= BESTANDEN else " ❌")
        lines.append(f"| {v['woche']} | {q} | {v['erledigt']} | {v['nachholen']} ({v['sp_nach']}) |")
    lines += ["", f"<!-- verlauf:{json.dumps(verlauf)}-->"]
    gh.update_issue(issue["number"], body="\n".join(lines))


def main(argv=None, gh=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("modus", choices=["start", "abschluss"])
    p.add_argument("--woche")
    p.add_argument("--heute")
    a = p.parse_args(argv)
    wochen = load("wochen.json")
    stories = load("stories.json")
    if a.woche:
        idx = next(i for i, w in enumerate(wochen) if w["id"] == a.woche)
    else:
        heute = date.fromisoformat(a.heute) if a.heute else heute_berlin()
        idx = woche_fuer(wochen, heute, a.modus)
        if idx is None:
            print(f"{heute}: kein Wochen{a.modus} fällig – nichts zu tun.")
            return
    if gh is None:
        from github_api import GitHub
        gh = GitHub()
    (start if a.modus == "start" else abschluss)(gh, wochen, stories, idx)


if __name__ == "__main__":
    main()
