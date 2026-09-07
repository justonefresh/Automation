#!/usr/bin/env python3
"""Run an authorized Playwright page check and write one JSON result per run."""

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


def is_valid_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return parsed_url.scheme in {"http", "https"} and bool(parsed_url.netloc)


def check_page(browser, url: str, timeout_ms: int) -> dict:
    executed_at = datetime.now(timezone.utc).isoformat()
    page = browser.new_page(
        user_agent="Automation-PoC-Monitor/1.0 (authorized synthetic check)"
    )
    result = {
        "execution_time": executed_at,
        "url_requested": url,
        "url_reached": None,
        "http_status": None,
        "page_title": None,
        "success": False,
        "error": None,
    }

    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        result["url_reached"] = page.url
        result["http_status"] = response.status if response else None
        result["page_title"] = page.title()
        result["success"] = bool(response and 200 <= response.status < 400)
        if not result["success"]:
            result["error"] = "HTTP response was not successful"
    except PlaywrightError as error:
        result["url_reached"] = page.url
        result["error"] = str(error)
    finally:
        page.close()

    return result


def write_html_report(results: list[dict], output: Path) -> None:
        """Write a readable HTML report containing every check result."""
        successful = sum(result["success"] for result in results)
        failed = len(results) - successful
        rows = []
        for result in results:
                status = "Passed" if result["success"] else "Failed"
                status_class = "pass" if result["success"] else "fail"
                rows.append(
                        "<tr>"
                        f"<td>{html.escape(result['execution_time'])}</td>"
                        f"<td>{html.escape(result['url_requested'])}</td>"
                        f"<td>{html.escape(result['url_reached'] or '-')}</td>"
                        f"<td>{result['http_status'] or '-'}</td>"
                        f"<td>{html.escape(result['page_title'] or '-')}</td>"
                        f'<td class="{status_class}">{status}</td>'
                        f"<td>{html.escape(result['error'] or '-')}</td>"
                        "</tr>"
                )

        report = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Article monitor results</title>
    <style>
        :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
        body {{ margin: 2rem auto; max-width: 1400px; padding: 0 1rem; }}
        h1 {{ margin-bottom: .25rem; }}
        .summary {{ color: #666; margin-top: 0; }}
        .pass {{ color: #16803c; font-weight: 700; }}
        .fail {{ color: #c62828; font-weight: 700; }}
        .table-wrap {{ overflow-x: auto; }}
        table {{ border-collapse: collapse; min-width: 900px; width: 100%; }}
        th, td {{ border: 1px solid #bbb; padding: .6rem; text-align: left; vertical-align: top; }}
        th {{ background: #eee; }}
        @media (prefers-color-scheme: dark) {{
            .summary {{ color: #aaa; }}
            th {{ background: #333; }}
            th, td {{ border-color: #666; }}
        }}
    </style>
</head>
<body>
    <h1>Article monitor results</h1>
    <p class="summary">{successful} passed, {failed} failed, {len(results)} total</p>
    <div class="table-wrap">
        <table>
            <thead><tr><th>Executed</th><th>Requested URL</th><th>Reached URL</th><th>HTTP</th><th>Title</th><th>Status</th><th>Error</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </div>
</body>
</html>
"""
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Authorized URL to monitor")
    parser.add_argument("--runs", type=int, default=1, help="Number of checks to run")
    parser.add_argument(
        "--timeout-ms", type=int, default=30_000, help="Navigation timeout in milliseconds"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("monitor-results.jsonl"), help="JSONL output path"
    )
    parser.add_argument(
        "--html-output", type=Path, default=Path("monitor-results.html"), help="HTML report path"
    )
    args = parser.parse_args()

    if not is_valid_url(args.url):
        print(f"Invalid URL: {args.url}", file=sys.stderr)
        return 2
    if args.runs < 1:
        print("--runs must be at least 1", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            with args.output.open("w", encoding="utf-8") as output:
                for _ in range(args.runs):
                    result = check_page(browser, args.url, args.timeout_ms)
                    results.append(result)
                    output.write(json.dumps(result) + "\n")
                    print(json.dumps(result))
                    failures += not result["success"]
        finally:
            browser.close()

    write_html_report(results, args.html_output)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())