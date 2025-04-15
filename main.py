# amazon_facebook_deal_bot/main.py

import requests
from bs4 import BeautifulSoup
import time
import os
import random
from dotenv import load_dotenv

# === LOAD SECRETS ===
load_dotenv()

AMAZON_URL = "https://www.amazon.com/gp/goldbox"
AFFILIATE_TAG = "?tag=keithw.-20"  # Updated affiliate tag
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POST_LIMIT = 3
USER_AGENT = {"User-Agent": "Mozilla/5.0"}

# === SAFETY CHECK FOR MISSING SECRETS ===
if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
    raise ValueError("FB_PAGE_ID or FB_ACCESS_TOKEN is missing! Check your .env file or GitHub Secrets.")

# === CATEGORY/KEYWORD-BASED HASHTAGS ===
CATEGORY_TAGS = {
    "tablet": ["#TabletDeal", "#KidsTech"],
    "fire": ["#AmazonFire", "#TechOnSale"],
    "candy": ["#SweetDeals", "#SnackAttack"],
    "alexa": ["#SmartHome", "#AlexaDeals"],
    "electronics": ["#GadgetDeals", "#TechSavvy"]
}

DEFAULT_HASHTAGS = ["#AmazonDeals", "#DailyDeals", "#HotBuy", "#LimitedTimeOffer"]


def generate_hashtags(title):
    tags = set(DEFAULT_HASHTAGS)
    title_lower = title.lower()
    for keyword, custom_tags in CATEGORY_TAGS.items():
        if keyword in title_lower:
            tags.update(custom_tags)
    return " ".join(random.sample(list(tags), min(len(tags), 5)))


def get_deals():
    print("[INFO] Scraping Amazon's Deals page...")
    response = requests.get(AMAZON_URL, headers=USER_AGENT)
    soup = BeautifulSoup(response.text, "html.parser")

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
            image_tag = link_tag.find("img")
            image_url = image_tag["src"] if image_tag and image_tag.has_attr("src") else None

            if not raw_link or raw_link in seen or not title:
                continue
            seen.add(raw_link)
            full_link = f"https://www.amazon.com{raw_link}{AFFILIATE_TAG}"
            extracted_deals.append((title, full_link, image_url))
            if len(extracted_deals) >= POST_LIMIT:
                return extracted_deals

    return extracted_deals


def post_to_facebook(title, link, image_url=None):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    hashtags = generate_hashtags(title)
    payload = {
        "caption": f"🔥 Deal Alert!\n{title}\n👉 {link}\n\n{hashtags}",
        "access_token": FB_ACCESS_TOKEN
    }
    if image_url:
        payload["url"] = image_url

    response = requests.post(url, data=payload)
    print("[FB POST]", response.json())


def main():
    print("[BOT STARTED] Fetching Amazon deals...")
    deals = get_deals()
    print(f"[INFO] Found {len(deals)} deals.")
    for title, link, image_url in deals:
        print("[POSTING]", title)
        post_to_facebook(title, link, image_url)
        time.sleep(10)


if __name__ == "__main__":
    main()
