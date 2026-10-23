import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / "paypal_pos.db"

# Default PayPal settings
DEFAULT_PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # "sandbox" or "live"
DEFAULT_PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
DEFAULT_PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")

# Store Defaults
DEFAULT_STORE_NAME = os.getenv("STORE_NAME", "NovaTech Retail & Fintech")
DEFAULT_TAX_RATE = float(os.getenv("DEFAULT_TAX_RATE", "8.0"))  # in percent
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
DEFAULT_CURRENCY_SYMBOL = "$"
