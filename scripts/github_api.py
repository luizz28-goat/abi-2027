"""Kleiner GitHub-REST-Client ohne Abhängigkeiten (nur Standardbibliothek).

Braucht GITHUB_TOKEN und GITHUB_REPOSITORY (owner/repo) – in GitHub Actions sind beide gesetzt.
Der Token wird nie ausgegeben.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

API = "https://api.github.com"


class GitHub:
    def __init__(self, repo: str | None = None, token: str | None = None):
        self.repo = repo or os.environ["GITHUB_REPOSITORY"]
        self.token = token or os.environ["GITHUB_TOKEN"]

    def request(self, method: str, path: str, body: dict | None = None):
        url = path if path.startswith("http") else f"{API}{path}"
        data = None if body is None else json.dumps(body).encode()
        for attempt in range(5):
            req = urllib.request.Request(url, data=data, method=method, headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "abi-2027-bot",
                **({"Content-Type": "application/json"} if data is not None else {}),
            })
            try:
                with urllib.request.urlopen(req) as resp:
                    raw = resp.read().decode()
                    link = resp.headers.get("Link", "")
                    if method != "GET":
                        time.sleep(1.0)  # sekundäre Rate-Limits beim Anlegen vieler Issues
                    return (json.loads(raw) if raw else None), link
            except urllib.error.HTTPError as err:
                text = err.read().decode()
                if err.code in (403, 429) and "rate limit" in text.lower() and attempt < 4:
                    time.sleep(30 * (attempt + 1))
                    continue
                raise RuntimeError(f"{method} {path} -> {err.code}: {text[:300]}") from None
        raise RuntimeError(f"{method} {path}: zu viele Versuche")

    def get_all(self, path: str) -> list:
        sep = "&" if "?" in path else "?"
        url = f"{API}{path}{sep}per_page=100"
        items = []
        while url:
            page, link = self.request("GET", url)
            items.extend(page)
            url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part[part.index("<") + 1:part.index(">")]
                    # GitHub liefert Folgeseiten als /repositories/<id>/…; über Proxys nur /repos/<owner>/<repo>/… erlaubt
                    url = re.sub(r"/repositories/\d+/", f"/repos/{self.repo}/", url)
        return items

    # Bequeme Hilfen
    def r(self, path: str) -> str:
        return f"/repos/{self.repo}{path}"

    def issues(self, labels: str | None = None, state: str = "all") -> list:
        q = f"?state={state}" + (f"&labels={labels}" if labels else "")
        return [i for i in self.get_all(self.r(f"/issues{q}")) if "pull_request" not in i]

    def create_issue(self, title: str, body: str, labels: list[str], milestone: int | None = None) -> dict:
        payload = {"title": title, "body": body, "labels": labels}
        if milestone:
            payload["milestone"] = milestone
        return self.request("POST", self.r("/issues"), payload)[0]

    def update_issue(self, number: int, **fields) -> dict:
        return self.request("PATCH", self.r(f"/issues/{number}"), fields)[0]

    def comment(self, number: int, body: str) -> None:
        self.request("POST", self.r(f"/issues/{number}/comments"), {"body": body})


def marker(kind: str, value: str) -> str:
    return f"<!-- abi-{kind}: {value} -->"


def find_marker(body: str | None, kind: str) -> str | None:
    if not body:
        return None
    start = f"<!-- abi-{kind}: "
    if start not in body:
        return None
    rest = body.split(start, 1)[1]
    return rest.split(" -->", 1)[0].strip()
