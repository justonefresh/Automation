#!/usr/bin/env python3
"""Fetch and print a webpage using curl_cffi's Chrome TLS impersonation."""

import argparse
import html
import sys
from pathlib import Path
from urllib.parse import urlparse

from curl_cffi import requests
from curl_cffi.requests import RequestsError


def scrape(url: str, output: Path | None = None) -> int:
    """Fetch ``url``, print its HTML, and optionally write an HTML report."""
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        print(f"Invalid URL: {url}", file=sys.stderr)
        return 2

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
    args = parser.parse_args()
    return scrape(args.url, args.output)


if __name__ == "__main__":
    raise SystemExit(main())