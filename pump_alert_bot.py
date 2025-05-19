import requests
import time
import schedule
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def get_tokens_data():
    urls = [
        "https://api.dexscreener.com/latest/dex/pairs/uniswap",
        "https://api.dexscreener.com/latest/dex/pairs/pancakeswap"
    ]
    all_tokens = []
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            all_tokens += response.json().get("pairs", [])
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
    return all_tokens

def evaluate_token(token):
    score = 0
    try:
        volume = float(token.get("volume", {}).get("h1", 0))
        price_change = float(token.get("priceChange", {}).get("h1", 0))
        tx_count = int(token.get("txCount", {}).get("h1", 0))

        if volume > 100000: score += 2
        if price_change > 20: score += 3
        if tx_count > 100: score += 1
        if volume > 500000 and price_change > 50: score += 3
    except Exception as e:
        print(f"Error scoring token: {e}")
    return score

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def check_tokens():
    tokens = get_tokens_data()
    top_alerts = []

    for token in tokens:
        score = evaluate_token(token)
        if score >= 5:
            info = f"<b>{token.get('baseToken', {}).get('symbol', 'N/A')}</b>\n"
            info += f"Score: {score}\n"
            info += f"Price: ${token.get('priceUsd')}\n"
            info += f"1h Volume: ${token.get('volume', {}).get('h1', 0)}\n"
            info += f"1h Change: {token.get('priceChange', {}).get('h1', 0)}%\n"
            info += f"Pair: {token.get('url')}\n"
            top_alerts.append(info)

    for alert in top_alerts:
        send_telegram_message(alert)

schedule.every(5).minutes.do(check_tokens)

if __name__ == "__main__":
    print("Bot is running every 5 minutes...")
    while True:
        schedule.run_pending()
        time.sleep(1)
