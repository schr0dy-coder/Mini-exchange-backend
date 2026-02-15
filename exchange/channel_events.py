def broadcast_orderbook(symbol_name):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from .services.orderbook import get_order_book
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        order_book = get_order_book(symbol_name)
        group = f"orderbook_{symbol_name}"
        async_to_sync(channel_layer.group_send)(
            group, {"type": "orderbook_update", "data": order_book}
        )
    except Exception:
        pass


def broadcast_prices():
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from exchange.models import Symbol

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    data = [
        {
            "symbol": s.name,
            "price": str(s.last_price),
        }
        for s in Symbol.objects.all()
    ]

    async_to_sync(channel_layer.group_send)(
        "prices_stream",
        {
            "type": "prices_update",
            "data": data,
        },
    )
