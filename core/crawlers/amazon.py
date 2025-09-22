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
                    txt = b.inner_text().strip()
                    match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kg|ml|l|pcs?|pack)', txt, re.IGNORECASE)
                    if match:
                        data["quantity"] = match.group(0)
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

            # Additional details from the product details table
            try:
                table = page.query_selector("table.a-normal.a-spacing-micro")
                if table:
                    rows = table.query_selector_all("tr")
                    for row in rows:
                        tds = row.query_selector_all("td")
                        if len(tds) >= 2:
                            key = tds[0].inner_text().strip()
                            value = tds[1].inner_text().strip()
                            data[key] = value
            except:
                pass

            # Use Net Quantity if available
            if "Net Quantity" in data:
                data["quantity"] = data["Net Quantity"]

            # Images (from fullscreen popover and fallback methods)
            try:
                img_counter = 1
                downloaded_urls = set()  # Track downloaded URLs to avoid duplicates
                
                print("[DEBUG] Starting image extraction...")
                
                # First, try to get images from the fullscreen popover
                try:
                    # Look for various thumbnail button selectors
                    button_selectors = [
                        "button.a-button-thumbnail",
                        ".a-button-thumbnail",
                        "button[data-action='main-image-click']",
                        "#main-image-container",
                        ".a-dynamic-image-container"
                    ]
                    
                    thumbnail_button = None
                    for selector in button_selectors:
                        thumbnail_button = page.query_selector(selector)
                        if thumbnail_button:
                            print(f"[DEBUG] Found button with selector: {selector}")
                            break
                    
                    if thumbnail_button:
                        print("[DEBUG] Clicking thumbnail button...")
                        thumbnail_button.click()
                        
                        # Wait for popover to appear with multiple possible selectors
                        popover_selectors = [
                            ".a-popover-wrapper",
                            "#image-block-popover",
                            ".image-viewer-popover",
                            "[role='dialog']"
                        ]
                        
                        popover_found = False
                        for pop_selector in popover_selectors:
                            try:
                                page.wait_for_selector(pop_selector, timeout=3000)
                                print(f"[DEBUG] Popover found with selector: {pop_selector}")
                                popover_found = True
                                break
                            except:
                                continue
                        
                        if popover_found:
                            # Wait a bit more for images to load
                            page.wait_for_timeout(2000)
                            
                            # Try multiple selectors for fullscreen images
                            image_selectors = [
                                "img.fullscreen",
                                ".fullscreen img",
                                "[data-a-image-name] img",
                                ".image-viewer img",
                                ".a-popover img"
                            ]
                            
                            fullscreen_imgs = []
                            for img_selector in image_selectors:
                                imgs = page.query_selector_all(img_selector)
                                if imgs:
                                    print(f"[DEBUG] Found {len(imgs)} images with selector: {img_selector}")
                                    fullscreen_imgs.extend(imgs)
                            
                            # Remove duplicates
                            unique_imgs = []
                            seen_srcs = set()
                            for img in fullscreen_imgs:
                                src = img.get_attribute("src")
                                if src and src not in seen_srcs:
                                    unique_imgs.append(img)
                                    seen_srcs.add(src)
                            
                            print(f"[DEBUG] Processing {len(unique_imgs)} unique images")
                            
                            for img in unique_imgs:
                                src = img.get_attribute("src")
                                if src and src not in downloaded_urls and "gif" not in src.lower():
                                    print(f"[DEBUG] Downloading: {src}")
                                    path = download_image(src, TEMP_DIR, f"img{img_counter}")
                                    if path:
                                        data["images"].append(path)
                                        downloaded_urls.add(src)
                                        img_counter += 1
                                        print(f"[DEBUG] Successfully downloaded image {img_counter-1}")
                            
                            # Close the popover
                            try:
                                page.keyboard.press("Escape")
                                page.wait_for_timeout(1000)
                            except:
                                pass
                        else:
                            print("[DEBUG] No popover found after clicking")
                    else:
                        print("[DEBUG] No thumbnail button found")
                                
                except Exception as e:
                    print(f"[DEBUG] Fullscreen extraction failed: {e}")
                
                # Fallback 1: Extract from JavaScript ImageBlockATF data
                if img_counter <= 2:
                    print("[DEBUG] Trying JavaScript ImageBlockATF extraction...")
                    try:
                        script_content = page.content()
                        
                        # Find the ImageBlockATF data in script
                        start_marker = '"colorImages":{"initial":'
                        start_idx = script_content.find(start_marker)
                        if start_idx != -1:
                            print("[DEBUG] Found ImageBlockATF data")
                            start_idx += len(start_marker) - 1
                            bracket_count = 0
                            end_idx = start_idx
                            
                            for i, char in enumerate(script_content[start_idx:], start_idx):
                                if char == '[':
                                    bracket_count += 1
                                elif char == ']':
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        end_idx = i + 1
                                        break
                            
                            if end_idx > start_idx:
                                json_str = script_content[start_idx:end_idx]
                                try:
                                    import json
                                    color_images = json.loads(json_str)
                                    print(f"[DEBUG] Found {len(color_images)} images in JavaScript data")
                                    for img_data in color_images:
                                        if 'hiRes' in img_data and img_data['hiRes']:
                                            hires_url = img_data['hiRes']
                                            if hires_url not in downloaded_urls and "gif" not in hires_url.lower():
                                                print(f"[DEBUG] Downloading JS image: {hires_url}")
                                                path = download_image(hires_url, TEMP_DIR, f"img{img_counter}")
                                                if path:
                                                    data["images"].append(path)
                                                    downloaded_urls.add(hires_url)
                                                    img_counter += 1
                                except json.JSONDecodeError as je:
                                    print(f"[DEBUG] JSON decode error: {je}")
                        else:
                            print("[DEBUG] No ImageBlockATF data found")
                    except Exception as e:
                        print(f"[DEBUG] JavaScript extraction failed: {e}")
                
                # Fallback 2: Get main image and thumbnails
                if img_counter <= 2:
                    print("[DEBUG] Using final fallback methods...")
                    
                    # Get main image
                    main_img = page.query_selector("#main-image-container img")
                    if main_img:
                        main_src = main_img.get_attribute("src") or main_img.get_attribute("data-a-image-source")
                        if main_src and main_src not in downloaded_urls and "gif" not in main_src.lower():
                            print(f"[DEBUG] Downloading main image: {main_src}")
                            if "._SX" in main_src or "._SY" in main_src:
                                highres_main = re.sub(r'\._S[XY]\d+_', '._SL1500_', main_src)
                            else:
                                highres_main = main_src
                            path = download_image(highres_main, TEMP_DIR, f"img{img_counter}")
                            if path:
                                data["images"].append(path)
                                downloaded_urls.add(highres_main)
                                img_counter += 1
                    
                    # Get thumbnail images
                    thumbs = page.query_selector_all("#altImages img")
                    print(f"[DEBUG] Found {len(thumbs)} thumbnail images")
                    for t in thumbs:
                        src = t.get_attribute("src")
                        if src and "icon" not in src.lower() and src not in downloaded_urls and "gif" not in src.lower():
                            # Extract ASIN and construct high-res URL
                            parsed = urlparse(src)
                            path_parts = parsed.path.split('/I/')
                            if len(path_parts) > 1:
                                asin = path_parts[1].split('.')[0]
                                highres_url = f"https://m.media-amazon.com/images/I/{asin}._SL1500_.jpg"
                            else:
                                highres_url = src
                            
                            if highres_url not in downloaded_urls:
                                print(f"[DEBUG] Downloading thumbnail: {highres_url}")
                                path = download_image(highres_url, TEMP_DIR, f"img{img_counter}")
                                if path:
                                    data["images"].append(path)
                                    downloaded_urls.add(highres_url)
                                    img_counter += 1

                print(f"[DEBUG] Total images extracted: {len(data['images'])}")
                        
            except Exception as e:
                print(f"[ERROR] Image extraction failed: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"[ERROR] Crawl failed: {e}")

        finally:
            browser.close()

    return data
