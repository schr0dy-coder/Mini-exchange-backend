import random
import time
from decimal import Decimal
from threading import Thread
from django.db import transaction
from exchange.models import Symbol
from exchange.channel_events import broadcast_prices
from exchange.services.exchange_service import place_order
from django.contrib.auth.models import User
from exchange.models import Portfolio, Holding



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


def market_maker_loop():
    while True:
        symbols = Symbol.objects.all()
        mm = User.objects.get(username="market_maker")
        portfolio = Portfolio.objects.get(user=mm)

        for symbol in symbols:
            if not symbol.last_price:
                continue

            holding = Holding.objects.get(user=mm, symbol=symbol)

            last_price = symbol.last_price
            base_spread = last_price * Decimal("0.005")

            inventory_ratio = holding.available_quantity / Decimal("5000")

            if inventory_ratio > Decimal("1.2"):
                bias = Decimal("-0.002")
            elif inventory_ratio < Decimal("0.8"):
                bias = Decimal("0.002")
            else:
                bias = Decimal("0")

            buy_price = last_price * (Decimal("1") - Decimal("0.005") + bias)
            sell_price = last_price * (Decimal("1") + Decimal("0.005") + bias)

            # place small size quotes
            try:
                place_order(mm, symbol.name, "BUY", buy_price, 20)
                place_order(mm, symbol.name, "SELL", sell_price, 20)
            except:
                pass

        time.sleep(5)

