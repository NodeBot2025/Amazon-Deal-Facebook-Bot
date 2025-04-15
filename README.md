# Amazon Deal Facebook Bot 🤖🔥

This bot scrapes Amazon's daily deals and auto-posts them to your Facebook Page with your affiliate link.

## Features
- Scrapes top 3 Amazon deals
- Auto-posts to Facebook Page with tracking link
- Uses your Amazon Affiliate tag
- Loads secrets from `.env` file

## Setup

1. Clone this repo
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with:
   ```
   FB_PAGE_ID=your_facebook_page_id
   FB_ACCESS_TOKEN=your_facebook_access_token
   ```
4. Run the bot:
   ```
   python main.py
   ```

## Customize
- Edit `POST_LIMIT` in `main.py` to change how many deals are posted
- Add scheduling via `cron` or Windows Task Scheduler for automation

## Disclaimer
Use responsibly and abide by Amazon and Facebook’s TOS.
