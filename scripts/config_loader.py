import os
from dotenv import load_dotenv

# Load .env from config folder
env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(env_path)

# Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_IDS = [int(x) for x in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if x]

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY", "")
SOFASPORT_API_KEY = os.getenv("SOFASPORT_API_KEY", "")
