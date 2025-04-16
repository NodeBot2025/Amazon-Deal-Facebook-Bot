import requests
from bs4 import BeautifulSoup
import time
import os
import random
import re
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
    prices = [p.get_text(strip=True).replace("$", "") for p in prices if p.get_text(strip=True).startswith("$")]
    prices = list(dict.fromkeys(prices))
    if len(prices) >= 2:
        list_price, deal_price = prices[1], prices[0]
    elif prices:
        list_price = deal_price = prices[0]
    else:
        list_price = deal_price = None
    return list_price, deal_price


def calculate_discount(list_price, deal_price):
    try:
        list_val = float(list_price)
        deal_val = float(deal_price)
        discount = round((list_val - deal_val) / list_val * 100)
        return f"{discount}% off"
    except:
        return None


def get_image_url(product_block):
    img_tag = product_block.select_one("img")
    return img_tag.get("src") if img_tag else None


def clean_title(raw_text):
    cleaned = re.sub(r'(\$\d+(\.\d{2})?)|(Typical:)|(Limited time deal)', '', raw_text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def generate_hashtags(title):
    keywords = re.findall(r"\b[A-Z][a-z]+|[a-z]{4,}\b", title)
    seen = set()
    hashtags = []
    for word in keywords:
        tag = '#' + re.sub(r'[^a-zA-Z0-9]', '', word.title())
        if tag not in seen and len(tag) > 4:
            hashtags.append(tag)
            seen.add(tag)
        if len(hashtags) >= 6:
            break
    return ' '.join(hashtags)


def get_deals():
    soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser")
    all_blocks = soup.select("a[href*='/dp/']")
    random.shuffle(all_blocks)
    extracted = []

    print(f"[DEBUG] Found {len(all_blocks)} deal-ish links after shuffling.")

    for block in all_blocks:
        try:
            raw_text = block.get_text(strip=True)
            title = clean_title(raw_text)[:200]
            href = block.get("href")
            if not title or not href or "/dp/" not in href:
                continue

            affiliate_link = f"https://www.amazon.com{href.split('?')[0]}{AFFILIATE_TAG}"
            parent = block.find_parent("div")
            list_price, deal_price = extract_price_data(parent or block)
            image_url = get_image_url(parent or block)
            discount = calculate_discount(list_price, deal_price)
            hashtags = generate_hashtags(title)

            caption_lines = []
            caption_lines.append(title)
            if list_price and deal_price and discount:
                caption_lines.append(f"{discount} — List: ${list_price} | Deal: ${deal_price}")
            caption_lines.append(f"👉 {affiliate_link}")
            if hashtags:
                caption_lines.append(hashtags)

            caption = '\n'.join(caption_lines)
            extracted.append((caption, image_url))

            if len(extracted) >= POST_LIMIT:
                break
        except Exception as e:
            print("[ERROR parsing block]", e)

    return extracted


def post_to_facebook(caption, image_url):
    if image_url:
        url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
        payload = {
            "caption": caption,
            "url": image_url,
            "access_token": FB_ACCESS_TOKEN
        }
    else:
        url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
        payload = {
            "message": caption,
            "access_token": FB_ACCESS_TOKEN
        }

    response = requests.post(url, data=payload)
    print("[FB POST]", response.status_code, response.text)


def main():
    print("[BOT STARTED] Fetching Amazon deals...")
    deals = get_deals()

    if not deals:
        print("[INFO] No deals found — structure may have changed.")
    else:
        print(f"[INFO] Found {len(deals)} deals to post.")

    for caption, image_url in deals:
        print("[POSTING]", caption)
        post_to_facebook(caption, image_url)
        time.sleep(10)


if __name__ == "__main__":
    main()
