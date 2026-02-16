from decimal import Decimal
from django.db import transaction
from exchange.models import Order, Portfolio, Trade, Symbol, Holding
from exchange.services.matching_engine import match_order
from exchange.services.price_fetch import fetch_symbol_price
from django.utils import timezone
from exchange.services.settlement import settle_trade


@transaction.atomic
def place_order(user, symbol_name, side, price, quantity):

    portfolio = Portfolio.objects.select_for_update().get(user=user)

    symbol = Symbol.get_by_name(symbol_name)
    if symbol is None:
        raise ValueError(f"Symbol not found: {symbol_name!r}")

    # Ensure we have a reasonably fresh market price for validation
    # If symbol price is missing or older than 60 seconds, attempt a targeted fetch.
    if not symbol.last_price or not symbol.last_price_updated_at or (timezone.now() - symbol.last_price_updated_at).total_seconds() > 60:
        try:
            fetched = fetch_symbol_price(symbol.name)
            if fetched is not None:
                # refresh symbol instance
                symbol = Symbol.objects.get(pk=symbol.pk)
        except Exception:
            pass

    price = Decimal(str(price))
    quantity = int(quantity)

    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    if price <= 0:
        raise ValueError("Price must be positive.")

    # ===== PRICE BAND VALIDATION (±10%) =====
    if symbol.last_price is not None:
        market_price = Decimal(symbol.last_price)

        lower_limit = market_price * Decimal("0.90")
        upper_limit = market_price * Decimal("1.10")

        if price < lower_limit or price > upper_limit:
            raise ValueError(
                f"Order price ${price:.2f} is outside valid range. "
                f"Market price: ${market_price:.2f}. "
                f"Valid range: ${lower_limit:.2f} - ${upper_limit:.2f}"
            )
    # =========================================

    # ===== RESERVATION =====
    if side == "BUY":
        total_cost = price * quantity

        if portfolio.available_balance < total_cost:
            raise ValueError("Insufficient balance.")

        portfolio.available_balance -= total_cost
        portfolio.reserved_balance += total_cost
        portfolio.save()

    elif side == "SELL":
        holding, _ = Holding.objects.select_for_update().get_or_create(
            user=user,
            symbol=symbol
        )

        if holding.available_quantity < quantity:
            raise ValueError("Insufficient shares.")

        holding.available_quantity -= quantity
        holding.reserved_quantity += quantity
        holding.save()

    else:
        raise ValueError("Invalid order side.")

    # ===== CREATE ORDER =====
    new_order = Order.objects.create(
        user=user,
        symbol=symbol,
        side=side,
        price=price,
        quantity=quantity
    )

    # ===== FILTER BY SYMBOL =====
    buy_orders = Order.objects.filter(
        symbol=symbol,
        side="BUY",
        status__in=["OPEN", "PARTIAL"]
    ).order_by("-price", "created_at")

    sell_orders = Order.objects.filter(
        symbol=symbol,
        side="SELL",
        status__in=["OPEN", "PARTIAL"]
    ).order_by("price", "created_at")

    trades_data = match_order(new_order, buy_orders, sell_orders)

    affected_orders = {new_order}

    for trade_data in trades_data:
        trade = Trade.objects.create(
            buy_order=trade_data["buy_order"],
            sell_order=trade_data["sell_order"],
            price=trade_data["price"],
            quantity=trade_data["quantity"]
        )

        settle_trade(trade)

        affected_orders.add(trade_data["buy_order"])
        affected_orders.add(trade_data["sell_order"])

    for order in affected_orders:
        update_order_status(order)

    return new_order

def update_order_status(order):
    if order.filled_quantity >= order.quantity:
        order.status = 'FILLED'
    elif order.filled_quantity > 0:
        order.status = 'PARTIAL'
    else:
        order.status = 'OPEN'
    order.save(update_fields=["status"])


@transaction.atomic
def cancel_order(user, order_id):

    order = Order.objects.select_for_update().get(id=order_id)

    if order.user != user:
        raise ValueError("You can only cancel your own orders.")

    if order.status not in ["OPEN", "PARTIAL"]:
        raise ValueError("Only open or partial orders can be canceled.")

    remaining_qty = order.remaining_quantity
    portfolio = Portfolio.objects.select_for_update().get(user=user)

    if order.side == "BUY":
        refund = order.price * remaining_qty
        portfolio.available_balance += refund
        portfolio.reserved_balance -= refund
        portfolio.save()

    elif order.side == "SELL":
        holding = Holding.objects.select_for_update().get(
            user=user,
            symbol=order.symbol
        )

        holding.available_quantity += remaining_qty
        holding.reserved_quantity -= remaining_qty
        holding.save()

    order.status = "CANCELED"
    order.save(update_fields=["status"])

    return order
