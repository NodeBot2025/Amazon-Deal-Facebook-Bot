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
    soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser")
    deals = soup.select(".DealContent")[:POST_LIMIT]
    extracted_deals = []

    for deal in deals:
        try:
            title_tag = deal.select_one(".DealTitle")
            link_tag = deal.select_one("a")
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                raw_link = link_tag.get("href")
                affiliate_link = f"https://www.amazon.com{raw_link}{AFFILIATE_TAG}"
                extracted_deals.append((title, affiliate_link))
        except Exception as e:
            print("[ERROR] Failed to parse a deal:", e)

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
    for title, link in deals:
        print("[POSTING]", title)
        post_to_facebook(title, link)
        time.sleep(10)


if __name__ == "__main__":
    main()
