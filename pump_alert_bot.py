import requests
import time
import schedule
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def get_tokens_data():
    """
    Fetch token pairs data from Dexscreener for Uniswap and PancakeSwap DEXs.
    Returns a list of token pairs.
    """
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
    """
    Score a token based on volume, price change, and transaction count.
    Returns an integer score.
    """
    score = 0
    try:
        volume = float(token.get("volume", {}).get("h1", 0))
        price_change = float(token.get("priceChange", {}).get("h1", 0))
        tx_count = int(token.get("txCount", {}).get("h1", 0))

        if volume > 100000:
            score += 2
        if price_change > 20:
            score += 3
        if tx_count > 100:
            score += 1
        if volume > 500000 and price_change > 50:
            score += 3
    except Exception as e:
        print(f"Error scoring token: {e}")
    return score

def send_telegram_message(message):
    """
    Send a message to the configured Telegram chat using the bot token.
    """
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
    """
    Main function to fetch tokens, evaluate them, and send alerts for high scores.
    """
    tokens = get_tokens_data()
    alerts = []

    for token in tokens:
        score = evaluate_token(token)
        if score >= 5:
            base_token = token.get('baseToken', {})
            symbol = base_token.get('symbol', 'N/A')
            price_usd = token.get('priceUsd', 'N/A')
            volume_1h = token.get('volume', {}).get('h1', 0)
            change_1h = token.get('priceChange', {}).get('h1', 0)
            url = token.get('url', 'N/A')

            message = (
                f"<b>{symbol}</b>\\n"
                f"Score: {score}\\n"
                f"Price: ${price_usd}\\n"
                f"1h Volume: ${volume_1h}\\n"
                f"1h Change: {change_1h}%\\n"
                f"Pair URL: {url}"
            )
            alerts.append(message)

    for alert in alerts:
        send_telegram_message(alert)

# Schedule the check every 5 minutes
schedule.every(5).minutes.do(check_tokens)

if __name__ == "__main__":
    print("Pump Alert Bot is running and checking every 5 minutes...")
    while True:
        schedule.run_pending()
        time.sleep(1)
