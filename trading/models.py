from django.db import models

# Model to store square-off rules.
class SquareOffRule(models.Model):
    # Trading symbol (e.g., NIFTY 50).
    symbol = models.CharField(max_length=100, help_text="Trading symbol (e.g., NIFTY 50)", null=True, blank=True)
    # Instrument token for the symbol, obtained from the broker (Zerodha Kite).
    instrument_token = models.CharField(max_length=100, help_text="Instrument token for the symbol (from broker)", null=True, blank=True)
    # Price at which the square-off should be triggered.
    lower_limit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price at which to trigger square-off if price falls below this level")
    upper_limit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price at which to trigger square-off if price rises above this level")
    # Flag to enable or disable the rule.
    active = models.BooleanField(default=True, help_text="Is this rule currently active?")
    # Flag to ensure the rule triggers only once per trading day.
    triggered_today = models.BooleanField(default=False, help_text="Has this rule been triggered today?")
    # If true, actions are logged but no actual orders are placed.
    dry_run = models.BooleanField(default=True, help_text="If true, log actions but do not place orders")
    # Global kill switch to instantly disable trading for this rule.
    kill_switch = models.BooleanField(default=False, help_text="If true, disable all trading instantly")

    # Timestamp for creation.
    created_at = models.DateTimeField(auto_now_add=True)
    # Timestamp for last update.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Options for the model, if any.
        pass

    def __str__(self):
        return f"{self.symbol} (Lower: {self.lower_limit_price}, Upper: {self.upper_limit_price}) (Active: {self.active})"

# Model to log all trading-related events.
class TradeLog(models.Model):
    # Foreign key to the SquareOffRule that initiated the event (can be null).
    rule = models.ForeignKey(SquareOffRule, on_delete=models.SET_NULL, null=True, blank=True)
    # Timestamp of the event.
    timestamp = models.DateTimeField(auto_now_add=True)
    # Type of event (e.g., TICK, TRIGGER, ORDER_PLACED, ORDER_FAILED).
    event_type = models.CharField(max_length=50, help_text="e.g., TICK, TRIGGER, ORDER_PLACED, ORDER_FAILED")
    # Detailed message about the event.
    message = models.TextField()
    # Additional JSON data related to the event (e.g., order parameters, error details).
    data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.event_type} - {self.message}"