import random
import time
from decimal import Decimal
from threading import Thread
from django.db import transaction
from exchange.models import Symbol
from exchange.channel_events import broadcast_prices


SIMULATION_INTERVAL = 1  # seconds


def simulate_price(symbol):
    last_price = symbol.last_price or Decimal("100.00")

    # ±0.3% random move
    change_pct = Decimal(random.uniform(-0.003, 0.003))
    new_price = last_price * (Decimal("1.0") + change_pct)

    # Clamp to avoid crash
    if new_price <= 1:
        new_price = Decimal("1.00")

    symbol.last_price = new_price.quantize(Decimal("0.01"))
    symbol.save(update_fields=["last_price"])


def simulation_loop():
    while True:
        symbols = list(Symbol.objects.all())
        for symbol in symbols:
            simulate_price(symbol)
        broadcast_prices()
        time.sleep(SIMULATION_INTERVAL)
