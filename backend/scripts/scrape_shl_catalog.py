"""
Starter scraper for SHL Individual Test Solutions.

Important:
- Check SHL robots.txt and terms before scraping.
- This file is intentionally conservative. For final submission, replace the sample
  catalog with the full Individual Test Solutions catalog.
"""
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "shl_catalog.json"


def scrape_catalog() -> list[dict]:
    response = requests.get(BASE_URL, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    items: list[dict] = []
    # Update selectors after inspecting the current SHL page HTML.
    for link in soup.select("a[href*='/solutions/products/product-catalog/view/']"):
        name = link.get_text(" ", strip=True)
        href = link.get("href", "")
        if not name or not href:
            continue
        url = href if href.startswith("http") else f"https://www.shl.com{href}"
        items.append({
            "name": name,
            "url": url,
            "test_type": "",
            "description": "",
            "skills": [],
            "job_family": [],
            "duration": ""
        })

    deduped = {item["url"]: item for item in items}
    return list(deduped.values())


if __name__ == "__main__":
    catalog = scrape_catalog()
    OUTPUT_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(catalog)} catalog items to {OUTPUT_PATH}")
