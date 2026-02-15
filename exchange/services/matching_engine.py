def match_order(new_order, buy_orders, sell_orders):
    """
    Pure matching logic.
    Does NOT write to DB.
    Does NOT modify portfolios.
    Only updates filled_quantity in memory.
    Returns list of trade dictionaries.
    """
    trades = []
    if new_order.side == "BUY":
        opposite_orders = sell_orders
    else:
        opposite_orders = buy_orders
    for opposite in opposite_orders:
        if new_order.remaining_quantity <= 0:
            break
        if opposite.remaining_quantity <= 0:
            continue
        price_match = False
        if new_order.side == "BUY" and new_order.price >= opposite.price:
            price_match = True
        elif new_order.side == "SELL" and new_order.price <= opposite.price:
            price_match = True
        if not price_match:
            break
        trade_quantity = min(
            new_order.remaining_quantity, 
            opposite.remaining_quantity
        )
        new_order.filled_quantity += trade_quantity
        opposite.filled_quantity += trade_quantity

        trades.append({
            'buy_order': new_order if new_order.side == "BUY" else opposite,
            'sell_order': new_order if new_order.side == "SELL" else opposite,
            'price': opposite.price,  # Trade executes at opposite order's price
            'quantity': trade_quantity
        })

    return trades