#!/usr/bin/env python3
"""Append scrape statuses to history and regenerate the committed HTML report."""

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


def update_report(
    results_dir: Path,
    history_path: Path,
    report_path: Path,
    target_url: str,
    workflow_run: str,
    total: int,
) -> None:
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    executed_at = datetime.now(timezone.utc).isoformat()

    for status_path in sorted(
        results_dir.glob("status-*.txt"),
        key=lambda path: int(path.stem.split("-")[1]),
    ):
        execution = status_path.stem.split("-")[1]
        history.append(
            {
                "executed_at": executed_at,
                "workflow_run": workflow_run,
                "execution": execution,
                "total": total,
                "url": target_url,
                "status": status_path.read_text(encoding="utf-8"),
            }
        )

    history_path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    succeeded = sum(entry["status"] == "Succeeded" for entry in history)
    rows = []
    for entry in reversed(history):
        status_class = "success" if entry["status"] == "Succeeded" else "failure"
        rows.append(
            "<tr>"
            f"<td>{html.escape(entry['executed_at'])}</td>"
            f"<td>{html.escape(entry['workflow_run'])}</td>"
            f"<td>{html.escape(entry['execution'])} of {entry['total']}</td>"
            f"<td>{html.escape(entry['url'])}</td>"
            f'<td class="{status_class}">{html.escape(entry["status"])}</td>'
            "</tr>"
        )

    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scrape results</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1200px; padding: 0 1rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #bbb; padding: .6rem; text-align: left; vertical-align: top; }}
    th {{ background: #eee; }}
    .success {{ color: #16803c; font-weight: 700; }}
    .failure {{ color: #c62828; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Scrape results</h1>
  <p>{succeeded} of {len(history)} total scrapes succeeded.</p>
  <table>
    <thead><tr><th>Executed</th><th>Workflow run</th><th>Scrape</th><th>URL</th><th>Status</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
    report_path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("scrape-results"))
    parser.add_argument("--history", type=Path, default=Path("scrape-history.json"))
    parser.add_argument("--report", type=Path, default=Path("index.html"))
    parser.add_argument("--url", required=True)
    parser.add_argument("--workflow-run", required=True)
    parser.add_argument("--total", type=int, required=True)
    args = parser.parse_args()
    update_report(
        args.results_dir,
        args.history,
        args.report,
        args.url,
        args.workflow_run,
        args.total,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
