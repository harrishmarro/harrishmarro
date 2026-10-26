#!/usr/bin/env python3
"""Update the recent-repositories block in the profile README."""

import html
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USERNAME = "harrishmarro"
README = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- RECENT-REPOS:START -->"
END = "<!-- RECENT-REPOS:END -->"
MAX_PROJECTS = 3
MAX_AGE_DAYS = 730
DESCRIPTION_OVERRIDES = {
    "Retail-Mesh-Intelligence": "A web tool for managing retail and dealer data",
}


def fetch_repositories():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-readme-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed",
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def recent_projects(repositories):
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    candidates = []
    for repository in repositories:
        if (
            repository.get("fork")
            or repository.get("archived")
            or repository.get("name", "").lower() == USERNAME
        ):
            continue
        if not repository.get("description") or not repository.get("pushed_at"):
            continue
        pushed = datetime.fromisoformat(repository["pushed_at"].replace("Z", "+00:00"))
        if pushed >= cutoff:
            candidates.append((pushed, repository))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[:MAX_PROJECTS]


def render(projects):
    if not projects:
        return "_New public project updates will appear here._"
    lines = []
    for pushed, repository in projects:
        name = html.escape(repository["name"])
        url = html.escape(repository["html_url"], quote=True)
        description = DESCRIPTION_OVERRIDES.get(
            repository["name"], repository["description"].strip().rstrip(".")
        )
        description = html.escape(description)
        updated = pushed.strftime("%B %d, %Y").replace(" 0", " ")
        lines.append(f"- **[{name}]({url})** — {description}. _Updated {updated}._")
    return "\n".join(lines)


def main():
    content = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(content):
        raise RuntimeError("Recent repository markers are missing from README.md")
    block = f"{START}\n{render(recent_projects(fetch_repositories()))}\n{END}"
    updated = pattern.sub(block, content, count=1)
    if updated != content:
        README.write_text(updated, encoding="utf-8")
        print("Updated recent public work in README.md")
    else:
        print("README.md is already current")


if __name__ == "__main__":
    main()
