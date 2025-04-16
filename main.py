import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

# === LOAD SECRETS ===
load_dotenv()

AMAZON_URL = "https://www.amazon.com/gp/goldbox"
AFFILIATE_TAG = "?tag=keithw.-20"
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POST_LIMIT = 5
USER_AGENT = {"User-Agent": "Mozilla/5.0"}


def extract_price_data(block):
    prices = block.select(".a-offscreen")
    prices = [p.get_text(strip=True) for p in prices if p.get_text(strip=True).startswith("$")]
    return prices[1] if len(prices) > 1 else None, prices[0] if prices else None


def get_deals():
    soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser")
    all_blocks = soup.select("a[href*='/dp/']")
    extracted = []

    print(f"[DEBUG] Found {len(all_blocks)} deal-ish links.")

    for block in all_blocks:
        try:
            title = block.get_text(strip=True)
            href = block.get("href")
            if not title or not href or "/dp/" not in href:
                continue

            affiliate_link = f"https://www.amazon.com{href.split('?')[0]}{AFFILIATE_TAG}"
            parent = block.find_parent("div")
            list_price, deal_price = extract_price_data(parent or block)

            formatted_title = f"{title}\nList: {list_price or 'N/A'} | Deal: {deal_price or 'N/A'}"
            extracted.append((formatted_title, affiliate_link))

            if len(extracted) >= POST_LIMIT:
                break
        except Exception as e:
            print("[ERROR parsing block]", e)

    return extracted


def post_to_facebook(title, link):
    payload = {
        "message": f"🔥 Deal Alert!\n{title}\n👉 {link}",
        "access_token": FB_ACCESS_TOKEN
    }
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
    response = requests.post(url, data=payload)
    print("[FB POST]", response.status_code, response.text)


def main():
    print("[BOT STARTED] Fetching Amazon deals...")
    deals = get_deals()

    if not deals:
        print("[INFO] No deals found — structure may have changed.")
    else:
        print(f"[INFO] Found {len(deals)} deals to post.")

    for title, link in deals:
        print("[POSTING]", title)
        post_to_facebook(title, link)
        time.sleep(10)


if __name__ == "__main__":
    main()
