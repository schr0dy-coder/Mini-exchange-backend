from django.db import transaction
from exchange.models import Portfolio, Holding
from exchange.channel_events import broadcast_orderbook, broadcast_prices
from django.utils import timezone

@transaction.atomic
def settle_trade(trade):

    buyer = trade.buy_order.user
    seller = trade.sell_order.user
    symbol = trade.buy_order.symbol

    trade_quantity = trade.quantity
    trade_price = trade.price
    buyer_order_price = trade.buy_order.price

    buyer_portfolio = Portfolio.objects.select_for_update().get(user=buyer)
    seller_portfolio = Portfolio.objects.select_for_update().get(user=seller)

    reserved_amount = buyer_order_price * trade_quantity
    actual_cost = trade_price * trade_quantity
    refund = reserved_amount - actual_cost

    # Buyer money
    buyer_portfolio.reserved_balance -= reserved_amount
    buyer_portfolio.available_balance += refund

    # Buyer shares
    buyer_holding, _ = Holding.objects.select_for_update().get_or_create(
        user=buyer,
        symbol=symbol
    )
    buyer_holding.available_quantity += trade_quantity

    # Seller shares
    seller_holding = Holding.objects.select_for_update().get(
        user=seller,
        symbol=symbol
    )
    seller_holding.reserved_quantity -= trade_quantity

    # Seller money
    seller_portfolio.available_balance += actual_cost

    # Save financial state first
    buyer_portfolio.save()
    seller_portfolio.save()
    buyer_holding.save()
    seller_holding.save()

    # Update market price last
    symbol.last_price = trade_price
    symbol.last_price_updated_at = timezone.now()
    symbol.save(update_fields=["last_price", "last_price_updated_at"])

    # Broadcast after everything committed
    broadcast_prices()
