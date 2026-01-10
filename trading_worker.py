import os
import django
import logging
import threading
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------- Django setup ----------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "st2026.settings")
django.setup()

from trading.models import SquareOffRule, TradeLog
from squareoff_execution import SquareOffExecutor
from kiteconnect import KiteConnect, KiteTicker

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trading_worker.log"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

# ---------------- Kite credentials ----------------
API_KEY = os.environ.get("KITE_API_KEY")
ACCESS_TOKEN = os.environ.get("KITE_ACCESS_TOKEN")

if not API_KEY or not ACCESS_TOKEN:
    logger.critical("KITE_API_KEY or KITE_ACCESS_TOKEN missing")
    exit(1)

try:
    kite.profile()
    logger.info("Kite REST authentication verified")
except Exception as e:
    logger.critical(f"Kite REST authentication failed: {e}", exc_info=True)
    exit(1)

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)




kws = KiteTicker(API_KEY, ACCESS_TOKEN)

# ---------------- Globals ----------------
# Global variables to store active instrument tokens and their last known prices.
ACTIVE_INSTRUMENT_TOKENS = set() # Stores unique instrument tokens to subscribe to.
LAST_PRICES = {} # Dictionary to store last price for each instrument_token.
ACTIVE_RULES_CACHE = [] # Cache for active square-off rules.
CACHE_LOCK = threading.Lock() # Lock to protect access to ACTIVE_RULES_CACHE.

# ---------------- Helper Functions ----------------
def get_instrument_tokens_from_rules():
    """Fetches all unique instrument tokens from active SquareOffRules."""
    global ACTIVE_INSTRUMENT_TOKENS
    unique_tokens = set()
    with CACHE_LOCK:
        for rule in ACTIVE_RULES_CACHE:
            if rule.instrument_token:
                unique_tokens.add(int(rule.instrument_token))

    # Also include any instrument tokens that are manually set or default, if applicable
    # For now, we're relying solely on rules for tokens.

    if unique_tokens != ACTIVE_INSTRUMENT_TOKENS:
        logger.info(f"Detected changes in instrument tokens. Old: {ACTIVE_INSTRUMENT_TOKENS}, New: {unique_tokens}")
        ACTIVE_INSTRUMENT_TOKENS = unique_tokens
        # If tokens change, we might need to re-subscribe. This will be handled in on_connect.
    return list(ACTIVE_INSTRUMENT_TOKENS)


# ---------------- DB helpers (SYNC) ----------------
def refresh_active_rules():
    """Fetches and caches active SquareOffRules from the Django database and updates subscribed instrument tokens."""
    global ACTIVE_RULES_CACHE
    with CACHE_LOCK:
        ACTIVE_RULES_CACHE = list(
            SquareOffRule.objects.filter(active=True, kill_switch=False)
        )
    logger.info(f"Loaded {len(ACTIVE_RULES_CACHE)} active rules")
    # After refreshing rules, update the list of instrument tokens to subscribe to.
    get_instrument_tokens_from_rules()

def log_trade(event, message, data=None):
    TradeLog.objects.create(
        event_type=event,
        message=message,
        data=data or {},
    )

# ---------------- Square-off logic ----------------
def evaluate_and_execute(instrument_token, price):
    """Evaluates square-off rules for a given instrument and triggers execution if conditions are met."""
    triggered_rules = []

    with CACHE_LOCK:
        # Filter rules relevant to the current instrument token
        relevant_rules = [
            rule for rule in ACTIVE_RULES_CACHE
            if str(rule.instrument_token) == str(instrument_token)
        ]

    for rule in relevant_rules:
        if rule.kill_switch or rule.triggered_today:
            continue

        trigger_met = False
        if rule.lower_limit_price and price <= rule.lower_limit_price:
            logger.warning(
                f"TRIGGERED (Lower Limit) rule {rule.id} {rule.symbol} @ {price} <= {rule.lower_limit_price}"
            )
            trigger_met = True
        elif rule.upper_limit_price and price >= rule.upper_limit_price:
            logger.warning(
                f"TRIGGERED (Upper Limit) rule {rule.id} {rule.symbol} @ {price} >= {rule.upper_limit_price}"
            )
            trigger_met = True

        if trigger_met:
            log_trade(
                "TRIGGER_CONDITION_MET",
                f"{rule.symbol} price {price} triggered rule {rule.id}",
                {"rule_id": rule.id, "instrument_token": instrument_token, "current_price": price},
            )
            triggered_rules.append(rule)

    if not triggered_rules:
        return

    dry_run = any(r.dry_run for r in triggered_rules)
    executor = SquareOffExecutor(API_KEY, ACCESS_TOKEN, dry_run=dry_run)

    for rule in triggered_rules:
        rule.triggered_today = True
        rule.save(update_fields=["triggered_today"])
        logger.info(f"Rule {rule.id} ({rule.symbol}) marked as triggered_today.")

    executor.square_off_all_option_positions()

# ---------------- WebSocket callbacks ----------------
def on_connect(ws, response):
    """Callback function for successful WebSocket connection."""
    logger.info("WebSocket connected. Subscribing to instruments...")

    # Subscribe to all active instrument tokens.
    tokens_to_subscribe = list(ACTIVE_INSTRUMENT_TOKENS)
    if tokens_to_subscribe:
        ws.subscribe(tokens_to_subscribe)
        ws.set_mode(ws.MODE_LTP, tokens_to_subscribe)
        logger.info(f"Subscribed to {len(tokens_to_subscribe)} instrument(s): {tokens_to_subscribe}")
    else:
        logger.warning("No active instrument tokens found in rules to subscribe.")

def on_ticks(ws, ticks):
    """Callback function for receiving live ticks from the WebSocket."""
    for tick in ticks:
        instrument_token = tick.get("instrument_token")
        last_price = tick.get("last_price")

        if instrument_token and last_price is not None:
            LAST_PRICES[instrument_token] = last_price
            logger.info(f"Price for {instrument_token}: {last_price}")
            evaluate_and_execute(instrument_token, last_price)

def on_close(ws, code, reason):
    logger.warning(f"WebSocket closed with code {code}: {reason}. Attempting to reconnect...")

def on_error(ws, code, reason):
    logger.error(f"WebSocket error with code {code}: {reason}")

# ---------------- Main ----------------
def main():
    logger.info("Starting trading worker")

    refresh_active_rules() # Initial load of rules and instrument tokens.

    kws.on_connect = on_connect
    kws.on_ticks = on_ticks
    kws.on_close = on_close
    kws.on_error = on_error

    kws.connect(threaded=True)
    logger.info("KiteTicker running")

    while True:
        time.sleep(60) # Periodically refresh rules
        refresh_active_rules()

if __name__ == "__main__":
    main()
