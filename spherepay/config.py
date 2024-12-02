from decimal import Decimal

# Database
DATABASE_URL = "postgresql://inventory_user:inventory_pass@db:5432/inventory_db"

# Margin rates
TRANSACTION_MARGIN_RATE = Decimal("0.001")  # 0.1%

# Settlement times (seconds)
SETTLEMENT_TIMES = {
    "USD": 3,
    "EUR": 2,
    "JPY": 3,
    "GBP": 2,
    "AUD": 3
}

# Initial pool balances
INITIAL_BALANCES = {
    "USD": 1_000_000,
    "EUR": 921_658,
    "JPY": 109_890_110,
    "GBP": 750_000,
    "AUD": 1_349_528
}

# Rebalancing settings
REBALANCE_HIGH_UTILIZATION = Decimal("0.7")    # 70%
REBALANCE_LOW_UTILIZATION = Decimal("0.3")     # 30%
REBALANCE_BUFFER_MULTIPLIER = Decimal("1.5")   # 50% extra
REBALANCE_INTERVAL_SECONDS = 60                # 1 minute
METRICS_WINDOW_HOURS = 1                       # 1 hour window