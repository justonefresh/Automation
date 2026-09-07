#!/usr/bin/env python3
"""Fetch and print a webpage using curl_cffi's Chrome TLS impersonation."""

import argparse
import html
import sys
from pathlib import Path
from urllib.parse import urlparse

from curl_cffi import requests
from curl_cffi.requests import RequestsError


def scrape(
    url: str, output: Path | None = None, scroll: bool = False
) -> int:
    """Fetch ``url``, print its HTML, and optionally write an HTML report."""
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        print(f"Invalid URL: {url}", file=sys.stderr)
        return 2

    if scroll:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                previous_height = 0
                stable_rounds = 0
                while stable_rounds < 3:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(500)
                    current_height = page.evaluate("document.body.scrollHeight")
                    if current_height == previous_height:
                        stable_rounds += 1
                    else:
                        stable_rounds = 0
                    previous_height = current_height
                page.evaluate("window.scrollTo(0, 0)")
                content = page.content()
                browser.close()
        except ImportError:
            print(
                "Browser scraping requires Playwright; install requirements.txt first.",
                file=sys.stderr,
            )
            return 1
        except PlaywrightError as error:
            print(f"Browser scrape failed: {error}", file=sys.stderr)
            return 1
    else:
        try:
            response = requests.get(
                url,
                impersonate="chrome",
                timeout=30,
                allow_redirects=True,
            )
            response.raise_for_status()
        except RequestsError as error:
            print(f"Request failed: {error}", file=sys.stderr)
            return 1
        content = response.text

    print(content, end="")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>Scrape result: {html.escape(url)}</title></head>"
            f"<body><h1>Scrape result</h1><p><a href=\"{html.escape(url, quote=True)}\">"
            f"{html.escape(url)}</a></p>{content}</body></html>\n",
            encoding="utf-8",
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="The webpage URL to scrape")
    parser.add_argument("--output", type=Path, help="Write the fetched page to an HTML file")
    parser.add_argument(
        "--scroll",
        action="store_true",
        help="Use a browser to scroll from the top to the bottom before capturing the page",
    )
    args = parser.parse_args()
    return scrape(args.url, args.output, args.scroll)


if __name__ == "__main__":
    raise SystemExit(main())