# amazon_facebook_deal_bot/main.py

import requests
from bs4 import BeautifulSoup
import time
import os
import random
import re
from datetime import datetime
from dotenv import load_dotenv

# === LOAD SECRETS ===
load_dotenv()

AMAZON_URL = "https://www.amazon.com/deals?bubble-id=trending-bubble"
AFFILIATE_TAG = "?tag=keithw.-20"
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POST_LIMIT = 3
USER_AGENT = {"User-Agent": "Mozilla/5.0"}
POSTED_FILE = "posted_asins.txt"

# === SAFETY CHECK ===
if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
    raise ValueError("FB_PAGE_ID or FB_ACCESS_TOKEN is missing! Check your .env or GitHub Secrets.")

CATEGORY_TAGS = { "tablet": ["#TabletDeal", "#KidsTech"], "fire": ["#AmazonFire", "#TechOnSale"], "candy": ["#SweetDeals", "#SnackAttack"], "alexa": ["#SmartHome", "#AlexaDeals"], "electronics": ["#GadgetDeals", "#TechSavvy"], "laptop": ["#LaptopDeals", "#RemoteWork"], "gaming": ["#GamerDeals", "#GameNight"], "home": ["#HomeEssentials", "#HouseholdSavings"], "kitchen": ["#KitchenDeals", "#HomeChef"], "pet": ["#PetCare", "#PetDeals"], "toy": ["#ToySale", "#FamilyFun"], "fitness": ["#FitLife", "#HomeWorkout"], "security": ["#HomeSecurity", "#SafeAndSmart"] }
DEFAULT_HASHTAGS = ["#AmazonDeals", "#DailyDeals", "#HotBuy", "#LimitedTimeOffer", "#FlashSale", "#PrimeFinds", "#DealHunters", "#BudgetBuys"]
TRENDING_TAGS = ["#TrendingNow", "#ViralDeals", "#MustHave", "#SmartShopping"]


def generate_hashtags(title):
    tags = set(DEFAULT_HASHTAGS)
    title_lower = title.lower()
    for keyword, custom_tags in CATEGORY_TAGS.items():
        if keyword in title_lower:
            tags.update(custom_tags)
    tags.update(random.sample(TRENDING_TAGS, k=1))
    return " ".join(random.sample(list(tags), min(len(tags), 6)))


def clean_title(title):
    title = re.sub(r'\$(\d+\.\d{2})\.\d{2}', r'\$\1', title)
    title = re.sub(r'(\$\d+(\.\d{2})?)\1+', r'\1', title)
    title = re.sub(r'(\$\d+(\.\d{2})?)\$?\d{2,}', r'\1', title)
    list_price_match = re.search(r'(List:\s*)\$\d+(\.\d{2})?\.\d{2}', title)
    if list_price_match:
        correct_price = re.search(r'(\$\d+(\.\d{2})?)', title)
        if correct_price:
            title = re.sub(r'List:\s*\$\d+(\.\d{2})?\.\d{2}', f"List: {correct_price.group(1)}", title)
    title = re.sub(r'(\d)([A-Z])', r'\1 \2', title)
    title = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', title)
    return title.strip()


def clean_amazon_url(raw_link):
    match = re.search(r"/dp/([A-Z0-9]{10})", raw_link)
    if match:
        return match.group(1), f"https://www.amazon.com/dp/{match.group(1)}{AFFILIATE_TAG}"
    return None, None


def reset_posted_file_weekly():
    today = datetime.utcnow()
    week_file = f"week_{today.strftime('%Y_%U')}.marker"
    if not os.path.exists(week_file):
        open(POSTED_FILE, 'w').close()
        with open(week_file, 'w') as f:
            f.write('reset')


def load_posted_asins():
    reset_posted_file_weekly()
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE, "r") as file:
        return set(line.strip() for line in file if line.strip())


def save_posted_asin(asin):
    asins = load_posted_asins()
    if asin not in asins:
        with open(POSTED_FILE, "a") as file:
            file.write(f"{asin}\n")


def get_deals():
    print("[INFO] Scraping Amazon's Trending Deals page...")
    response = requests.get(AMAZON_URL, headers=USER_AGENT)
    soup = BeautifulSoup(response.text, "html.parser")
    selectors = ["a[href*='/dp/']"]
    extracted_deals, seen = [], set()
    posted_asins = load_posted_asins()

    for selector in selectors:
        deal_links = soup.select(selector)
        for link_tag in deal_links:
            raw_link = link_tag.get("href")
            title = clean_title(link_tag.get_text(strip=True))
            image_tag = link_tag.find("img")
            image_url = image_tag["src"] if image_tag and image_tag.has_attr("src") else None
            asin, clean_link = clean_amazon_url(raw_link)
            if not asin or asin in posted_asins or asin in seen or not title:
                continue
            seen.add(asin)
            extracted_deals.append((asin, title, clean_link, image_url))
            if len(extracted_deals) >= POST_LIMIT:
                return extracted_deals

    return extracted_deals


def post_to_facebook(asin, title, link, image_url=None):
    hashtags = generate_hashtags(title)
    if image_url:
        url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
        payload = {
            "caption": f"🔥 Deal Alert!\n{title}\n👉 {link}\n\n{hashtags}",
            "access_token": FB_ACCESS_TOKEN,
            "url": image_url
        }
    else:
        url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
        payload = {
            "message": f"🔥 Deal Alert!\n{title}\n👉 {link}\n\n{hashtags}",
            "access_token": FB_ACCESS_TOKEN
        }
    response = requests.post(url, data=payload)
    print("[FB POST]", response.json())
    save_posted_asin(asin)


def main():
    print("[BOT STARTED] Fetching Amazon deals...")
    deals = get_deals()
    print(f"[INFO] Found {len(deals)} new deals.")
    for asin, title, link, image_url in deals:
        print("[POSTING]", title)
        post_to_facebook(asin, title, link, image_url)
        time.sleep(10)


if __name__ == "__main__":
    main()
