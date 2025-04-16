import requests from bs4 import BeautifulSoup import time import os from dotenv import load_dotenv

=== LOAD SECRETS ===

load_dotenv()

AMAZON_URL = "https://www.amazon.com/gp/goldbox" AFFILIATE_TAG = "?tag=keithw.-20" FB_PAGE_ID = os.getenv("FB_PAGE_ID") FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN") POST_LIMIT = 3 USER_AGENT = {"User-Agent": "Mozilla/5.0"}

def extract_price_data(product_soup): try: list_price_tag = product_soup.select_one('.a-price.a-text-price span.a-offscreen') list_price = list_price_tag.get_text(strip=True) if list_price_tag else None

deal_price_tag = product_soup.select_one('.a-price:not(.a-text-price) span.a-offscreen')
    deal_price = deal_price_tag.get_text(strip=True) if deal_price_tag else None

    return list_price, deal_price
except Exception as e:
    print("[ERROR parsing price]", e)
    return None, None

def get_deals(): soup = BeautifulSoup(requests.get(AMAZON_URL, headers=USER_AGENT).text, "html.parser") deals = soup.select(".DealCardModule")[:POST_LIMIT] extracted_deals = []

print(f"[DEBUG] Found {len(deals)} potential card modules.")

for deal in deals:
    try:
        title_tag = deal.select_one(".a-spacing-mini") or deal.select_one("h2")
        link_tag = deal.select_one("a[href]")
        title = title_tag.get_text(strip=True) if title_tag else "[NO TITLE FOUND]"
        raw_link = link_tag.get("href") if link_tag else None
        affiliate_link = f"https://www.amazon.com{raw_link}{AFFILIATE_TAG}" if raw_link else None

        list_price, deal_price = extract_price_data(deal)
        print(f"[DEBUG] {title} | List: {list_price} | Deal: {deal_price}")

        formatted_title = f"{title}\nList: {list_price or 'N/A'} | Deal: {deal_price or 'N/A'}"
        if title and affiliate_link:
            extracted_deals.append((formatted_title, affiliate_link))
        else:
            print("[WARN] Skipping due to missing title or link.")
    except Exception as e:
        print("[ERROR] Failed to parse a deal:", e)

return extracted_deals

def post_to_facebook(title, link): payload = { "message": f"🔥 Deal Alert!\n{title}\n👉 {link}", "access_token": FB_ACCESS_TOKEN } url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed" response = requests.post(url, data=payload) print("[FB POST]", response.status_code, response.text)

def main(): print("[BOT STARTED] Fetching Amazon deals...") deals = get_deals()

if not deals:
    print("[INFO] No deals found at all — check selectors or page structure.")
else:
    print(f"[INFO] Found {len(deals)} deals to post.")

for title, link in deals:
    print("[POSTING]", title)
    post_to_facebook(title, link)
    time.sleep(10)

if name == "main": main()

