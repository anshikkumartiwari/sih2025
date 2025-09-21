from core.crawlers import amazon

def process_product(url: str):
    # currently only supports Amazon
    if "amazon" in url.lower():
        return amazon.crawl(url)
    return {"error": "Unsupported platform"}
