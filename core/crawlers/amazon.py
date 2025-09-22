# Crawler module
# core/crawlers/amazon.py
import os
import re
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs


TEMP_DIR = os.path.join("temp", "temp2")
os.makedirs(TEMP_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)[:100]


def download_image(url: str, folder: str, prefix: str):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            basename = os.path.basename(urlparse(url).path)
            name, ext = os.path.splitext(basename)
            sanitized_name = sanitize_filename(name)
            filename = f"{prefix}_{sanitized_name}{ext}"
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                f.write(r.content)
            return filepath
    except Exception as e:
        print(f"[WARN] Failed to download {url}: {e}")
    return None


def crawl(url: str):
    data = {
        "url": url,
        "title": None,
        "mrp": None,
        "quantity": None,
        "manufacturer": None,
        "origin": None,
        "images": []
    }

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Title
            try:
                data["title"] = page.query_selector("#productTitle").inner_text().strip()
            except:
                pass

            # MRP (Price)
            for sel in ["#priceblock_ourprice", "#priceblock_dealprice", "span.a-price span.a-offscreen"]:
                el = page.query_selector(sel)
                if el:
                    data["mrp"] = el.inner_text().strip()
                    break

            # Quantity (look in bullet points or description)
            try:
                bullets = page.query_selector_all("#feature-bullets li span.a-list-item")
                for b in bullets:
                    txt = b.inner_text().strip().lower()
                    if any(unit in txt for unit in ["g", "kg", "ml", "l", "pack of", "pcs"]):
                        data["quantity"] = txt
                        break
            except:
                pass

            # Manufacturer / Packer / Importer (in detail section)
            try:
                rows = page.query_selector_all("#productDetails_techSpec_section_1 tr, #productDetails_detailBullets_sections1 tr")
                for row in rows:
                    heading = row.query_selector("th").inner_text().strip().lower()
                    val = row.query_selector("td").inner_text().strip()
                    if "manufacturer" in heading:
                        data["manufacturer"] = val
                    if "country of origin" in heading:
                        data["origin"] = val
            except:
                pass

            # Images (from image block JSON or thumbnails)
            try:
                thumbs = page.query_selector_all("#altImages img")
                for i, t in enumerate(thumbs):
                    src = t.get_attribute("src")
                    if src:
                        # Extract ASIN and construct high-res URL
                        parsed = urlparse(src)
                        path_parts = parsed.path.split('/I/')
                        if len(path_parts) > 1:
                            asin = path_parts[1].split('.')[0]
                            highres_url = f"https://m.media-amazon.com/images/I/{asin}._SL1500_.jpg"
                        else:
                            highres_url = src  # fallback
                        path = download_image(highres_url, TEMP_DIR, f"img{i+1}")
                        if path:
                            data["images"].append(path)
            except:
                pass

        except Exception as e:
            print(f"[ERROR] Crawl failed: {e}")

        finally:
            browser.close()

    return data
