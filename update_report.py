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
            f'<td><span class="status {status_class}">{html.escape(entry["status"])}</span></td>'
            "</tr>"
        )

        report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scrape results</title>
  <style>
        :root {{
            color-scheme: light;
            --ink: #17212b;
            --muted: #667382;
            --line: #d9e0e7;
            --surface: #ffffff;
            --canvas: #f5f7f9;
            --success: #176b45;
            --success-bg: #e9f5ee;
            --failure: #a33a34;
            --failure-bg: #fbeceb;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            background: var(--canvas);
            color: var(--ink);
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            line-height: 1.5;
            margin: 0;
            padding: 3rem 1.25rem;
        }}
        main {{ margin: 0 auto; max-width: 1200px; }}
        .page-header {{ margin-bottom: 1.5rem; }}
        h1 {{ font-size: clamp(1.6rem, 3vw, 2.15rem); margin: 0; }}
        .subtitle {{ color: var(--muted); margin: .4rem 0 0; }}
        .summary {{
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 2px 8px rgb(23 33 43 / 5%);
            margin-bottom: 1rem;
            padding: 1rem 1.15rem;
        }}
        .table-shell {{
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 2px 8px rgb(23 33 43 / 5%);
            overflow-x: auto;
        }}
        table {{ border-collapse: collapse; min-width: 760px; width: 100%; }}
        th, td {{ border-bottom: 1px solid var(--line); padding: .8rem 1rem; text-align: left; vertical-align: top; }}
        th {{ background: #f8fafb; color: var(--muted); font-size: .75rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; white-space: nowrap; }}
        tr:last-child td {{ border-bottom: 0; }}
        tbody tr:hover {{ background: #fbfcfd; }}
        td {{ font-size: .92rem; }}
        td:nth-child(1), td:nth-child(2), td:nth-child(3) {{ white-space: nowrap; }}
        td:nth-child(4) {{ max-width: 32rem; overflow-wrap: anywhere; }}
        .status {{ display: inline-flex; border-radius: 999px; font-size: .78rem; font-weight: 700; padding: .2rem .55rem; }}
        .success {{ background: var(--success-bg); color: var(--success); }}
        .failure {{ background: var(--failure-bg); color: var(--failure); }}
        @media (max-width: 640px) {{ body {{ padding: 2rem .75rem; }} th, td {{ padding: .7rem .8rem; }} }}
  </style>
</head>
<body>
    <main>
        <header class="page-header">
            <h1>Scrape results</h1>
            <p class="subtitle">A cumulative record of automated and manual page checks.</p>
        </header>
        <section class="summary" aria-label="Summary"><strong>{succeeded} of {len(history)} scrapes succeeded.</strong></section>
        <div class="table-shell">
            <table>
                <thead><tr><th>Executed</th><th>Workflow run</th><th>Scrape</th><th>URL</th><th>Status</th></tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    </main>
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
