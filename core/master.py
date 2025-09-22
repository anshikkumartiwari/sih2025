from core.crawlers import amazon

def process_product(url: str):
    if any(domain in url.lower() for domain in ["amazon", "amzn.in"]):
        return amazon.crawl(url)
    return {"error": "Unsupported platform"}