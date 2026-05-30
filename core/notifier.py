import os
import requests
import logging

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Telegram bot token and chat ID must be set in environment variables.")

def send_notification(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send notification: {e}")
