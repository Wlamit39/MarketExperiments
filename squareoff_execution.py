import logging
from kiteconnect import KiteConnect
from trading.models import TradeLog

logger = logging.getLogger(__name__)


class SquareOffExecutor:
    """
    Handles fetching positions, filtering option positions,
    and placing square-off orders.
    (SYNC-ONLY, production safe)
    """

    def __init__(self, api_key, access_token, dry_run=True):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.dry_run = dry_run
        logger.info(f"SquareOffExecutor initialized. Dry run={self.dry_run}")

    # ---------------- Positions ----------------
    def fetch_open_positions(self):
        """Fetch all net open positions."""
        try:
            positions = self.kite.positions()
            return positions.get("net", [])
        except Exception as e:
            logger.error("Error fetching positions", exc_info=True)
            TradeLog.objects.create(
                event_type="POSITION_FETCH_FAILED",
                message=str(e),
            )
            return []

    def filter_option_positions(self, positions):
        """Return only option positions with non-zero quantity."""
        option_positions = []

        for p in positions:
            qty = p.get("quantity", 0)
            symbol = p.get("tradingsymbol", "")

            if qty == 0:
                continue

            # Zerodha options usually contain CE / PE
            if symbol.endswith("CE") or symbol.endswith("PE"):
                option_positions.append(p)

        return option_positions

    # ---------------- Orders ----------------
    def place_square_off_order(self, position):
        tradingsymbol = position.get("tradingsymbol")
        exchange = position.get("exchange")
        quantity = position.get("quantity")

        if not tradingsymbol or not exchange or not quantity:
            logger.error(f"Invalid position data: {position}")
            return False

        transaction_type = (
            self.kite.TRANSACTION_TYPE_BUY
            if quantity < 0
            else self.kite.TRANSACTION_TYPE_SELL
        )

        abs_quantity = abs(quantity)

        order_params = {
            "variety": self.kite.VARIETY_REGULAR,
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": abs_quantity,
            "product": self.kite.PRODUCT_MIS,
            "order_type": self.kite.ORDER_TYPE_MARKET,
            "validity": self.kite.VALIDITY_DAY,
        }

        logger.info(
            f"Square-off attempt {transaction_type} {abs_quantity} {tradingsymbol}"
        )

        TradeLog.objects.create(
            event_type="ORDER_ATTEMPT",
            message=f"{transaction_type} {abs_quantity} {tradingsymbol}",
            data=order_params,
        )

        if self.dry_run:
            logger.warning(f"DRY RUN – order not placed: {order_params}")
            return True

        try:
            order_id = self.kite.place_order(**order_params)
            logger.info(f"Order placed: {order_id}")

            TradeLog.objects.create(
                event_type="ORDER_PLACED",
                message=f"Order {order_id} placed",
                data={"order_id": order_id, "symbol": tradingsymbol},
            )
            return True

        except Exception as e:
            logger.error("Order placement failed", exc_info=True)
            TradeLog.objects.create(
                event_type="ORDER_FAILED",
                message=str(e),
                data={"symbol": tradingsymbol},
            )
            return False

    # ---------------- Square-off ----------------
    def square_off_all_option_positions(self):
        logger.info("Starting square-off for all option positions")

        positions = self.fetch_open_positions()
        option_positions = self.filter_option_positions(positions)

        if not option_positions:
            logger.info("No option positions to square off")
            TradeLog.objects.create(
                event_type="SQUARE_OFF",
                message="No open option positions",
            )
            return

        success = 0
        for position in option_positions:
            if self.place_square_off_order(position):
                success += 1

        TradeLog.objects.create(
            event_type="SQUARE_OFF_SUMMARY",
            message=f"Squared off {success}/{len(option_positions)} positions",
        )

        self._handle_partial_fills_and_retries(option_positions)

    # ---------------- Future extension ----------------
    def _handle_partial_fills_and_retries(self, positions):
        logger.warning(
            "Partial fills & retries not implemented (placeholder)"
        )
