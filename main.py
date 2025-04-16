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

AMAZON_URL = "https://www.amazon.com/gp/goldbox"
AFFILIATE_TAG = "?tag=keithw.-20"
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
POST_LIMIT = 5
USER_AGENT = {"User-Agent": "Mozilla/5.0"}

# === TEXT CONFIG ===
INTRO_LINES = [
    "Deal of the day!", "Check this out!", "Hot pick!",
    "Limited offer — don’t miss it!", "Just dropped!", "Fan favorite deal!"
]

SEASONAL_INTROS = {
    (1, 2): ["New Year. New Deals!"], (3, 4): ["Spring into savings!"],
    (5, 6): ["Summer savings unlocked!"], (7, 8): ["Back to school picks!"],
    (9, 10): ["Fall favorites on sale!"], (11, 12): ["Holiday gift idea!"]
}

CATEGORY_KEYWORDS = {
    "toys": ["Playtime pick!"], "tech": ["Gadget drop!"], "kitchen": ["Chef’s choice!"],
    "fitness": ["Stay active!"], "beauty": ["Glow-up deal!"], "fashion": ["Style steal!"],
    "home": ["Home upgrade!"], "office": ["Desk essential!"]
}

EMOJIS = {
    "toys": "🧸", "tech": "💻", "kitchen": "🍳", "fitness": "🏋️",
    "beauty": "💄", "fashion": "👗", "home": "🛋️", "office": "📎"
}

DISCOUNT_TIERS = [
    (50, ["🔥 Insane deal!"]), (30, ["Hot deal!"]), (15, ["Nice price drop!"]),
    (1,  ["Small discount — still worth it!"])
]

# === UTILITY FUNCTIONS ===

def extract_price_data(block):
    prices = block.select(".a-offscreen")
    clean = [p.get_text(strip=True).replace("$", "") for p in prices if "$" in p.text]
    clean = list(dict.fromkeys(clean))
    if len(clean) >= 2:
        return clean[1], clean[0]
    elif clean:
        return clean[0], clean[0]
    return None, None

def get_image_url(block):
    img = block.select_one("img")
    return img["src"] if img else None

def calculate_discount(list_price, deal_price):
    try:
        return f"{round((float(list_price) - float(deal_price)) / float(list_price) * 100)}% off"
    except:
        return None

def clean_title(text):
    text = re.sub(r'(?i)\b\d{1,3}%\s*off\b|\b\d{1,3}%\b|Limited time deal|Typical:|List:', '', text)
    text = re.sub(r'\$\d+(?:\.\d{2})?', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def generate_hashtags(title):
    words = re.findall(r"\b[A-Z][a-z]+|[a-z]{4,}\b", title)
    seen = set()
    tags = []
    for word in words:
        tag = "#" + re.sub(r'[^a-zA-Z0-9]', '', word.title())
        if tag not in seen and len(tag) > 4:
            tags.append(tag)
            seen.add(tag)
        if len(tags) >= 6:
            break
    return " ".join(tags)

def get_intro(title, discount):
    title_lower = title.lower()
    for keyword, phrases in CATEGORY_KEYWORDS.items():
        if keyword in title_lower:
            emoji = EMOJIS.get(keyword, "")
            category_intro = f"{emoji} {random.choice(phrases)}"
            break
    else:
        category_intro = random.choice(INTRO_LINES)

    try:
        discount_value = int(discount.split('%')[0])
    except:
        discount_value = 0

    for threshold, intros in DISCOUNT_TIERS:
        if discount_value >= threshold:
            return f"{random.choice(intros)} {category_intro}"
    return category_intro

# === FACEBOOK POST FUNCTION ===

def post_to_facebook(caption, image_url):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    payload = {
        "caption": caption,
        "url": image_url,
        "access_token": FB_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    print("[FB POST]", response.status_code, response.text)

# === MAIN DEAL SCRAPER ===

def get_deals():
    soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser")
    blocks = soup.select("a[href*='/dp/']")
    random.shuffle(blocks)

    deals = []
    seen = set()

    for block in blocks:
        try:
            text = block.get_text(strip=True)
            title = clean_title(text)
            href = block.get("href")
            if not title or not href or "/dp/" not in href:
                continue

            asin = href.split("/dp/")[1].split("/")[0].split("?")[0]
            if asin in seen:
                continue
            seen.add(asin)

            full_link = f"https://www.amazon.com/dp/{asin}{AFFILIATE_TAG}"
            parent = block.find_parent("div")

            list_price, deal_price = extract_price_data(parent or block)
            image_url = get_image_url(parent or block)
            discount = calculate_discount(list_price, deal_price)

            if not (title and discount and list_price and deal_price and image_url):
                continue

            intro = get_intro(title, discount)
            hashtags = generate_hashtags(title)

            caption = f"""{intro}
{discount}  {title}
{discount} — List: ${list_price} | Deal: ${deal_price}
👇 {full_link}

  
{hashtags}"""

            deals.append((caption, image_url))
            if len(deals) >= POST_LIMIT:
                break

        except Exception as e:
            print("[ERROR BLOCK]", e)

    return deals

# === MAIN LOOP ===

def main():
    print("[BOT STARTED]")
    deals = get_deals()

    if not deals:
        print("[INFO] No deals found.")
        return

    for caption, image_url in deals:
        print("[POSTING DEAL]")
        post_to_facebook(caption, image_url)
        time.sleep(10)

if __name__ == "__main__":
    main()
