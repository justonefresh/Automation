# Article monitor PoC

This project scrapes an authorized webpage with `curl_cffi`. GitHub Actions runs the scraper at 100 privately selected times per UTC day and can also run it manually, saving each result as an HTML artifact.

## Local use

```bash
python -m pip install -r requirements.txt
python scrape.py https://example.com --scroll --output scrape-result.html
```

The command prints the fetched HTML to stdout and can also save it as an HTML page. With `--scroll`, Playwright scrolls from the top to the bottom first so lazy-loaded content is included; the complete scroll is counted as one scrape:

```bash
python scrape.py https://example.com --scroll --output scrape-result.html
```

## GitHub Actions

For automatic runs, create a repository variable named `TARGET_URL` containing the authorized URL. In GitHub, open **Settings > Secrets and variables > Actions > Variables > New repository variable** and set the name to `TARGET_URL`. The workflow checks every five minutes and selects 100 times per UTC day using an HMAC-based schedule. For a private, harder-to-predict schedule, add an optional repository secret named `SCHEDULE_SEED` under **Settings > Secrets and variables > Actions > Secrets**. Use a long random value. Unselected checks exit without scraping.

The workflow still supports manual runs from the **Actions** tab with a URL and an execution count. Manual runs always execute and do not wait for a random slot. After every selected or manual run, the workflow commits the cumulative `index.html` report and `scrape-history.json` to `main`. You can open `index.html` directly in the repository. The same files and individual page captures are also uploaded as the `scrape-results` artifact.