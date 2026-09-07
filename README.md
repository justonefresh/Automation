# Article monitor PoC

This project scrapes an authorized webpage with `curl_cffi`. GitHub Actions runs the scraper automatically every hour and can also run it manually, saving each result as an HTML artifact.

## Local use

```bash
python -m pip install -r requirements.txt
python scrape.py https://example.com --output scrape-result.html
```

The command prints the fetched HTML to stdout and can also save it as an HTML page:

```bash
python scrape.py https://example.com --output scrape-result.html
```

## GitHub Actions

Create a repository variable named `TARGET_URL` containing the authorized URL. The scheduled workflow runs one scrape hourly and uploads one HTML page per execution as the `scrape-results` artifact. Start it manually from the **Actions** tab with a URL and an execution count, or use the scheduled repository variable.