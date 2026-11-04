"""Collect a fixed, independent Lab04 sample from GitHub's public REST API.

Run from the repository root: python -m lab04.src.collect_ci_runs
No third-party GitHub client or Lab03 dataset is used.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPOSITORY = "fastapi/fastapi"
WORKFLOW_ID = 1929523  # .github/workflows/test.yml, named Test
WORKFLOW_NAME = "Test"
BRANCH = "master"
CREATED = "2026-07-01..2026-09-30"  # closed calendar quarter, UTC
EVENT = "push"
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "ci_runs.csv"
FIELDS = (
    "run_id", "created_at", "run_url", "repository", "workflow_id",
    "workflow_name", "branch", "conclusion", "failed",
)


def _fetch_page(page: int) -> dict:
    query = urlencode({
        "per_page": 100, "page": page, "branch": BRANCH,
        "status": "completed", "event": EVENT, "created": CREATED,
    })
    url = (
        f"https://api.github.com/repos/{REPOSITORY}/actions/"
        f"workflows/{WORKFLOW_ID}/runs?{query}"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Lab04-CI-research",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            return json.load(response)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"GitHub API request failed on page {page}: {exc}") from exc


def collect_ci_runs(path: str | Path = OUTPUT) -> dict:
    """Write every success/failure run in the fixed quarter; return counts."""
    first = _fetch_page(1)
    total = first["total_count"]
    if total > 1000:
        raise ValueError("GitHub search is capped at 1000 runs; narrow CREATED")
    pages = [first]
    for page in range(2, (total + 99) // 100 + 1):
        pages.append(_fetch_page(page))

    rows = []
    excluded = {}
    seen = set()
    for payload in pages:
        for run in payload["workflow_runs"]:
            run_id = int(run["id"])
            if run_id in seen:
                raise ValueError(f"Duplicate run returned by API: {run_id}")
            seen.add(run_id)
            if (run["workflow_id"] != WORKFLOW_ID or run["name"] != WORKFLOW_NAME
                    or run["head_branch"] != BRANCH or run["event"] != EVENT
                    or run["status"] != "completed"
                    or not "2026-07-01" <= run["created_at"][:10] <= "2026-09-30"):
                raise ValueError(f"Run outside the predefined sample: {run_id}")
            conclusion = run["conclusion"]
            if conclusion not in ("success", "failure"):
                key = str(conclusion)
                excluded[key] = excluded.get(key, 0) + 1
                continue
            rows.append({
                "run_id": run_id,
                "created_at": run["created_at"],
                "run_url": run["html_url"],
                "repository": REPOSITORY,
                "workflow_id": WORKFLOW_ID,
                "workflow_name": WORKFLOW_NAME,
                "branch": BRANCH,
                "conclusion": conclusion,
                "failed": int(conclusion == "failure"),
            })
    if len(seen) != total:
        raise ValueError(f"Incomplete pagination: received {len(seen)} of {total} runs")
    rows.sort(key=lambda row: (row["created_at"], row["run_id"]))
    if len(rows) < 30:
        raise ValueError(f"Insufficient sample: only {len(rows)} usable runs")

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(target)
    return {
        "queried": total, "n": len(rows),
        "k": sum(row["failed"] for row in rows), "excluded": excluded,
        "output": str(target),
    }


if __name__ == "__main__":
    print(json.dumps(collect_ci_runs(), ensure_ascii=False, indent=2))
