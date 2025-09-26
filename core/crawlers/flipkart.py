import os
import re
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

# Define TEMP_DIR using absolute path to ensure correct folder resolution
TEMP_DIR = os.path.join(os.path.dirname(_file_), "temp", "temp2")
os.makedirs(TEMP_DIR, exist_ok=True)

def sanitize_filename(name: str) -> str:
    """Sanitize filename to remove invalid characters and limit length."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)[:100]

def download_image(url: str, folder: str, prefix: str) -> str | None:
    """Download an image from a URL and save it to the specified folder."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0"}
        r = requests.get(url, timeout=10, headers=headers)
        if r.status_code == 200:
            basename = os.path.basename(urlparse(url).path)
            name, ext = os.path.splitext(basename)
            sanitized_name = sanitize_filename(name)
            filename = f"{prefix}_{sanitized_name}{ext}"
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                f.write(r.content)
            print(f"[INFO] Downloaded image to {filepath}")
            return filepath
        else:
            print(f"[WARN] Failed to download {url}: HTTP {r.status_code}")
            return None
    except Exception as e:
        print(f"[WARN] Failed to download {url}: {e}")
        return None

def crawl(url: str) -> dict:
    """Crawl a Flipkart product page and extract data, including images."""
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
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0")
        page = context.new_page()

        try:
            print(f"[INFO] Navigating to {url}")
            page.goto(url, timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(5000)  # Wait for dynamic content

            # Title
            try:
                title_elem = page.query_selector("span.VU-ZEz")
                data["title"] = title_elem.inner_text().strip() if title_elem else None
                print(f"[INFO] Title extracted: {data['title']}")
            except Exception as e:
                print(f"[WARN] Title extraction failed: {e}")

            # MRP (Price)
            for sel in ["div._3I9_wc._2p6lqe", "div.Nx9bqj.CxhGGd"]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        data["mrp"] = el.inner_text().strip()
                        print(f"[INFO] MRP extracted: {data['mrp']}")
                        break
                except Exception as e:
                    print(f"[WARN] MRP extraction failed for {sel}: {e}")

            # Quantity
            try:
                bullets = page.query_selector_all(".highlight-points ul li")
                for b in bullets:
                    txt = b.inner_text().strip()
                    match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kg|ml|l|pcs?|pack)', txt, re.IGNORECASE)
                    if match:
                        data["quantity"] = match.group(0)
                        print(f"[INFO] Quantity extracted: {data['quantity']}")
                        break
            except Exception as e:
                print(f"[WARN] Quantity extraction from bullets failed: {e}")

            # Fallback: Extract quantity from title
            if not data["quantity"] and data["title"]:
                match = re.search(r'\((\d+(?:\.\d+)?)\s*(g|kg|ml|l|pcs?|pack)\)', data["title"], re.IGNORECASE)
                if match:
                    data["quantity"] = match.group(1) + " " + match.group(2)
                    print(f"[INFO] Quantity extracted from title: {data['quantity']}")

            # Manufacturer and Origin
            try:
                dts = page.query_selector_all("dl._21lJbe dt")
                dds = page.query_selector_all("dl._21lJbe dd")
                for i in range(len(dts)):
                    heading = dts[i].inner_text().strip().lower()
                    val = dds[i].inner_text().strip() if i < len(dds) else None
                    if "manufactured by" in heading:
                        data["manufacturer"] = val
                        print(f"[INFO] Manufacturer extracted: {data['manufacturer']}")
                    if "country of origin" in heading:
                        data["origin"] = val
                        print(f"[INFO] Origin extracted: {data['origin']}")
            except Exception as e:
                print(f"[WARN] Manufacturer/Origin extraction failed: {e}")

            # Fallback: Table structure
            if not data["manufacturer"]:
                try:
                    rows = page.query_selector_all("div._3k-BhJ tr")
                    for row in rows:
                        heading = row.query_selector("th").inner_text().strip().lower()
                        val = row.query_selector("td").inner_text().strip()
                        if "manufactured by" in heading:
                            data["manufacturer"] = val
                            print(f"[INFO] Manufacturer extracted from table: {data['manufacturer']}")
                        if "country of origin" in heading:
                            data["origin"] = val
                            print(f"[INFO] Origin extracted from table: {data['origin']}")
                except Exception as e:
                    print(f"[WARN] Table extraction failed: {e}")

            # Additional details
            try:
                dts = page.query_selector_all("dl._21lJbe dt")
                dds = page.query_selector_all("dl._21lJbe dd")
                for i in range(len(dts)):
                    key = dts[i].inner_text().strip()
                    value = dds[i].inner_text().strip() if i < len(dds) else None
                    data[key] = value
                    if key == "Net Quantity":
                        data["quantity"] = value
                        print(f"[INFO] Quantity updated from details: {data['quantity']}")
            except Exception as e:
                print(f"[WARN] Additional details extraction failed: {e}")

            # Image Extraction
            try:
                img_counter = 1
                downloaded_urls = set()
                print("[INFO] Starting image extraction...")

                # Thumbnail images
                thumbs = page.query_selector_all("li.YGoYIP img")
                print(f"[INFO] Found {len(thumbs)} thumbnail images")
                for img in thumbs:
                    src = img.get_attribute("src")
                    if src and "gif" not in src.lower() and "rukminim" in src:
                        hires_url = re.sub(r'/\d+/\d+/', '/1280/1280/', src)
                        hires_url = re.sub(r'q=\d+', 'q=100', hires_url)
                        hires_url = hires_url.replace('&crop=false', '')
                        if hires_url not in downloaded_urls:
                            path = download_image(hires_url, TEMP_DIR, f"img{img_counter}")
                            if path:
                                data["images"].append(path)
                                downloaded_urls.add(hires_url)
                                img_counter += 1

                # Fallback: Main image
                if img_counter <= 1:
                    print("[INFO] Using fallback to main image...")
                    main_img = page.query_selector("img._396cs4")
                    if main_img:
                        src = main_img.get_attribute("src")
                        if src and "gif" not in src.lower():
                            hires_url = re.sub(r'/\d+/\d+/', '/1280/1280/', src)
                            hires_url = re.sub(r'q=\d+', 'q=100', hires_url)
                            hires_url = hires_url.replace('&crop=false', '')
                            if hires_url not in downloaded_urls:
                                path = download_image(hires_url, TEMP_DIR, f"img{img_counter}")
                                if path:
                                    data["images"].append(path)
                                    downloaded_urls.add(hires_url)
                                    img_counter += 1

                # Additional fallback: All relevant images
                if img_counter <= 1:
                    print("[INFO] Using additional fallback for images...")
                    all_imgs = page.query_selector_all('img[src*="rukminim2.flixcart.com/image/"]')
                    for img in all_imgs:
                        src = img.get_attribute("src")
                        if src and "gif" not in src.lower() and "original" in src:
                            hires_url = re.sub(r'/\d+/\d+/', '/1280/1280/', src)
                            hires_url = re.sub(r'q=\d+', 'q=100', hires_url)
                            hires_url = hires_url.replace('&crop=false', '')
                            if hires_url not in downloaded_urls:
                                path = download_image(hires_url, TEMP_DIR, f"img{img_counter}")
                                if path:
                                    data["images"].append(path)
                                    downloaded_urls.add(hires_url)
                                    img_counter += 1

                print(f"[INFO] Total images extracted: {len(data['images'])}")
            except Exception as e:
                print(f"[ERROR] Image extraction failed: {e}")

        except Exception as e:
            print(f"[ERROR] Crawl failed: {e}")
        finally:
            browser.close()

    return data
# Example usage
# if _name_ == "_main_":
#     sample_url = "https://www.flipkart.com/sunfeast-light-active-marie-biscuit/p/itmdae3b30067008?pid=CKBFSNTZHE8HVYPY&lid=LSTCKBFSNTZHE8HVYPYZXNM2W&marketplace=FLIPKART&q=biscuits&store=eat%2F5am&srno=s_1_3&otracker=search&otracker1=search&fm=Search&iid=687341b9-09cd-4485-837a-1cbce195a296.CKBFSNTZHE8HVYPY.SEARCH&ppt=sp&ppn=sp&ssid=9u9xo7caz40000001758836410068&qH=e046ebae628f52f3"
#     result = crawl(sample_url)
#     print("\n[RESULT] Extracted Data:")
#     print(result)