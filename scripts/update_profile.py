#!/usr/bin/env python3
"""Update public-repository highlights and a locally served activity card."""

import html
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USERNAME = "harrishmarro"
README = Path(__file__).resolve().parents[1] / "README.md"
ACTIVITY_CARD = README.parent / "assets" / "github-activity.svg"
START = "<!-- RECENT-REPOS:START -->"
END = "<!-- RECENT-REPOS:END -->"
MAX_PROJECTS = 3
MAX_AGE_DAYS = 730
EXCLUDED_REPOSITORIES = {"AI-regoginition"}
DESCRIPTION_OVERRIDES = {
    "Retail-Mesh-Intelligence": "A web tool for managing retail and dealer data",
    "Speaker-Independent-dysarthria-analysis": (
        "Speaker-independent dysarthria research with reproducible acoustic baselines"
    ),
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
    repositories = []
    page = 1
    while True:
        request = urllib.request.Request(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed&page={page}",
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def public_projects(repositories):
    return [repository for repository in repositories if not (
        repository.get("fork")
        or repository.get("archived")
        or repository.get("name") in EXCLUDED_REPOSITORIES
        or repository.get("name", "").lower() == USERNAME
    )]


def recent_projects(repositories):
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    candidates = []
    for repository in public_projects(repositories):
        if (not repository.get("description") and repository.get("name") not in
                DESCRIPTION_OVERRIDES) or not repository.get("pushed_at"):
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
            repository["name"], (repository.get("description") or "").strip().rstrip(".")
        )
        description = html.escape(description)
        updated = pushed.strftime("%B %d, %Y").replace(" 0", " ")
        lines.append(f"- **[{name}]({url})** — {description}. _Updated {updated}._")
    return "\n".join(lines)


def render_activity_svg(repositories):
    projects = public_projects(repositories)
    stars = sum(int(repository.get("stargazers_count") or 0) for repository in projects)
    latest = max(projects, key=lambda item: item.get("pushed_at") or "", default=None)
    latest_name = latest["name"] if latest else "Explore my repositories"
    if len(latest_name) > 22:
        latest_name = latest_name[:21] + "…"
    latest_name = html.escape(latest_name)
    description = html.escape(
        f"{len(projects)} public, non-archived projects; {stars} stars; "
        f"most recently updated project: {latest['name'] if latest else 'none'}"
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="780" height="176"
  viewBox="0 0 780 176" role="img" aria-labelledby="title description">
  <title id="title">Harish's public GitHub work</title>
  <desc id="description">{description}</desc>
  <rect width="780" height="176" rx="16" fill="#171b2e"/>
  <text x="28" y="36" fill="#a8b9ef" font-family="Arial,sans-serif"
    font-size="16">PUBLIC GITHUB WORK</text>
  <line x1="260" y1="55" x2="260" y2="145" stroke="#455071"/>
  <line x1="500" y1="55" x2="500" y2="145" stroke="#455071"/>
  <text x="28" y="102" fill="#79a7ff" font-family="Arial,sans-serif"
    font-size="42" font-weight="bold">{len(projects)}</text>
  <text x="28" y="136" fill="#d6ddf5" font-family="Arial,sans-serif"
    font-size="16">Public projects</text>
  <text x="286" y="102" fill="#79a7ff" font-family="Arial,sans-serif"
    font-size="42" font-weight="bold">{stars}</text>
  <text x="286" y="136" fill="#d6ddf5" font-family="Arial,sans-serif"
    font-size="16">Stars earned</text>
  <text x="526" y="91" fill="#79a7ff" font-family="Arial,sans-serif"
    font-size="19" font-weight="bold">{latest_name}</text>
  <text x="526" y="136" fill="#d6ddf5" font-family="Arial,sans-serif"
    font-size="16">Recently updated</text>
</svg>
'''


def main():
    content = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(content):
        raise RuntimeError("Recent repository markers are missing from README.md")
    repositories = fetch_repositories()
    block = f"{START}\n{render(recent_projects(repositories))}\n{END}"
    updated = pattern.sub(block, content, count=1)
    card = render_activity_svg(repositories)
    ACTIVITY_CARD.parent.mkdir(parents=True, exist_ok=True)
    if not ACTIVITY_CARD.exists() or ACTIVITY_CARD.read_text(encoding="utf-8") != card:
        ACTIVITY_CARD.write_text(card, encoding="utf-8")
        print("Updated public activity card")
    if updated != content:
        README.write_text(updated, encoding="utf-8")
        print("Updated recent public work in README.md")
    else:
        print("README.md is already current")


if __name__ == "__main__":
    main()
