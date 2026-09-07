#!/usr/bin/env python3
"""Fetch and print a webpage using curl_cffi's Chrome TLS impersonation."""

import argparse
import sys
from urllib.parse import urlparse

from curl_cffi import requests
from curl_cffi.requests import RequestsError


def scrape(url: str) -> int:
    """Fetch ``url`` and print its HTML, returning a process exit status."""
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

    print(response.text, end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="The webpage URL to scrape")
    args = parser.parse_args()
    return scrape(args.url)


if __name__ == "__main__":
    raise SystemExit(main())