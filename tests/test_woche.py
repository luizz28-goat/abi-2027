"""Testlauf für Wochenstart und -abschluss gegen ein simuliertes GitHub.

python3 -m unittest discover -s tests
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import woche  # noqa: E402
from github_api import marker  # noqa: E402


class FakeGitHub:
    def __init__(self):
        self.items = {}
        self.comments = []
        self.n = 0

    def _add(self, title, body, labels, state="open"):
        self.n += 1
        self.items[self.n] = {"number": self.n, "title": title, "body": body, "state": state,
                              "labels": [{"name": l} for l in labels]}
        return self.items[self.n]

    def issues(self, labels=None, state="all"):
        out = []
        for i in self.items.values():
            names = {l["name"] for l in i["labels"]}
            if labels and not set(labels.split(",")) <= names:
                continue
            out.append(json.loads(json.dumps(i)))
        return out

    def create_issue(self, title, body, labels, milestone=None):
        return self._add(title, body, labels)

    def update_issue(self, number, **fields):
        i = self.items[number]
        if "labels" in fields:
            i["labels"] = [{"name": l} for l in fields.pop("labels")]
        fields.pop("state_reason", None)
        i.update(fields)
        return i

    def comment(self, number, body):
        self.comments.append((number, body))


class WocheTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.stories = woche.load("stories.json")
        for s in self.stories:
            if s["woche"] in ("W02", "W03"):
                self.gh._add(f"[{s['woche']}] {s['titel']}", marker("story", s["id"]),
                             ["type:lernblock", f"woche:{s['woche']}", f"sp:{s['story_points']}"])
        self.gh._add("Fortschritt", marker("fortschritt", "main"), ["type:fortschritt"])

    def test_nachholen(self):
        woche.main(["start", "--woche", "W02"], gh=self.gh)
        test = next(i for i in self.gh.items.values() if "Wochentest" in i["title"])
        self.assertIn("F1 · US-", test["body"])
        w02 = [s for s in self.stories if s["woche"] == "W02"]
        nummern = {i["body"].split("abi-story: ")[1].split(" ")[0]: i["number"]
                   for i in self.gh.items.values() if "abi-story" in (i["body"] or "")}
        # Alle Blöcke erledigt bis auf den letzten; die erste Testfrage falsch, Rest richtig
        for s in w02[:-1]:
            self.gh.items[nummern[s["id"]]]["state"] = "closed"
        body = test["body"]
        zeilen = [z for z in body.splitlines() if z.startswith("- [ ] F")]
        for z in zeilen[1:]:
            body = body.replace(z, z.replace("- [ ]", "- [x]", 1))
        test["body"] = body

        woche.main(["abschluss", "--woche", "W02"], gh=self.gh)

        verschoben = [i for i in self.gh.items.values()
                      if any(l["name"] == "nachholen" for l in i["labels"]) and "abi-story" in i["body"]]
        ids = sorted(i["body"].split("abi-story: ")[1].split(" ")[0] for i in verschoben)
        erwartet = sorted([w02[-1]["id"]] + [s["id"] for s in w02 if s["testfrage"]][:1])
        self.assertEqual(ids, erwartet)
        for i in verschoben:
            self.assertIn("woche:W03", {l["name"] for l in i["labels"]})
            self.assertEqual(i["state"], "open")
        nachhol = [i for i in self.gh.items.values() if "Nachholblock" in i["title"]]
        self.assertEqual(len(nachhol), 1)
        fort = next(i for i in self.gh.items.values() if "abi-fortschritt" in i["body"])
        self.assertIn("W02", fort["body"])

        # Nächste Woche fragt die nachgeholten Blöcke erneut ab
        woche.main(["start", "--woche", "W03"], gh=self.gh)
        t3 = next(i for i in self.gh.items.values() if "[Wochentest W03]" in i["title"])
        for sid in erwartet:
            if next(s for s in self.stories if s["id"] == sid)["testfrage"]:
                self.assertIn(sid, t3["body"])
        self.assertIn("nachgeholt", t3["body"])

    def test_klausurphase(self):
        """Nach der Klausur wird nichts mehr verschoben; andere Fächer wandern in die nächste K-Woche."""
        gh = FakeGitHub()
        k05 = [s for s in self.stories if s["woche"] == "K05"]
        for s in k05:
            gh._add(f"[K05] {s['titel']}", marker("story", s["id"]), ["type:lernblock", "woche:K05", f"sp:{s['story_points']}"])
        gh._add("Fortschritt", marker("fortschritt", "main"), ["type:fortschritt"])
        woche.main(["start", "--woche", "K05"], gh=gh)
        woche.main(["abschluss", "--woche", "K05"], gh=gh)  # nichts erledigt, nichts richtig
        status = {i["body"].split("abi-story: ")[1].split(" ")[0]: i for i in gh.items.values() if "abi-story" in (i["body"] or "")}
        for s in k05:
            labels = {l["name"] for l in status[s["id"]]["labels"]}
            if s["fach"] == "Mathe":  # Mathe-Klausur am 09.11. = Start K06
                self.assertEqual(status[s["id"]]["state"], "closed", s["id"])
            else:
                self.assertIn("woche:K06", labels, s["id"])
                self.assertIn("nachholen", labels, s["id"])

    def test_wochenerkennung(self):
        wochen = woche.load("wochen.json")
        from datetime import date
        self.assertEqual(wochen[woche.woche_fuer(wochen, date(2027, 1, 11), "start")]["id"], "W02")
        self.assertEqual(wochen[woche.woche_fuer(wochen, date(2027, 4, 4), "abschluss")]["id"], "W12")
        self.assertIsNone(woche.woche_fuer(wochen, date(2027, 3, 28), "abschluss"))
        self.assertEqual(wochen[woche.woche_fuer(wochen, date(2026, 10, 5), "start")]["id"], "K01")
        self.assertEqual(wochen[woche.woche_fuer(wochen, date(2026, 12, 20), "abschluss")]["id"], "K11")
        self.assertIsNone(woche.woche_fuer(wochen, date(2027, 1, 3), "abschluss"))


if __name__ == "__main__":
    unittest.main()
