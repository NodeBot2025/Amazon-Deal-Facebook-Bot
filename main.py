# amazon_facebook_deal_bot/main.py

import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

# === LOAD SECRETS ===
load_dotenv()

AMAZON_URL = "https://www.amazon.com/gp/goldbox"
AFFILIATE_TAG = "?tag=keithw.-20"  # Updated affiliate tag
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POST_LIMIT = 3
USER_AGENT = {"User-Agent": "Mozilla/5.0"}


def get_deals():
    print("[INFO] Scraping Amazon's Deals page...")
    response = requests.get(AMAZON_URL, headers=USER_AGENT)
    soup = BeautifulSoup(response.text, "html.parser")

    # Try multiple strategies to find deals
    selectors = [
        "div.a-section.a-text-center > a[href*='/dp/']",
        "a[href*='/dp/']",
        "div.a-row.a-size-base.a-color-secondary > a[href*='/dp/']"
    ]

    extracted_deals = []
    seen = set()

    for selector in selectors:
        print(f"[DEBUG] Trying selector: {selector}")
        deal_links = soup.select(selector)

        for link_tag in deal_links:
            raw_link = link_tag.get("href")
            title = link_tag.get_text(strip=True)
            if not raw_link or raw_link in seen or not title:
                continue
            seen.add(raw_link)
            full_link = f"https://www.amazon.com{raw_link}{AFFILIATE_TAG}"
            extracted_deals.append((title, full_link))
            if len(extracted_deals) >= POST_LIMIT:
                return extracted_deals

    return extracted_deals


def post_to_facebook(title, link):
    payload = {
        "message": f"🔥 Deal Alert!\n{title}\n👉 {link}",
        "access_token": FB_ACCESS_TOKEN
    }
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
    response = requests.post(url, data=payload)
    print("[FB POST]", response.json())


def main():
    print("[BOT STARTED] Fetching Amazon deals...")
    deals = get_deals()
    print(f"[INFO] Found {len(deals)} deals.")
    for title, link in deals:
        print("[POSTING]", title)
        post_to_facebook(title, link)
        time.sleep(10)


if __name__ == "__main__":
    main()
