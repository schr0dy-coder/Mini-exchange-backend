from django.db.models import F, Sum
from exchange.models.symbol import Symbol
from exchange.models import Order


def get_order_book(symbol):
    """symbol: Symbol instance or symbol name (str). Resolves by name if str."""
    if not isinstance(symbol, Symbol):
        resolved = Symbol.get_by_name(symbol)
        if resolved is None:
            raise Symbol.DoesNotExist()
        symbol = resolved
    buy_book = (
        Order.objects.filter(
            side = 'BUY',
            status__in = ['OPEN', 'PARTIAL'],
            symbol = symbol
            
        )
        .annotate(
            remaining = F('quantity') - F('filled_quantity')
        )
        .values('price')
        .annotate(
            total_quantity = Sum('remaining')
        )
        .order_by('-price')
    )
    sell_book = (
        Order.objects.filter(
            side = 'SELL',
            status__in = ['OPEN', 'PARTIAL'],
            symbol = symbol
        )
        .annotate(
            remaining = F('quantity') - F('filled_quantity')
        )
        .values('price')
        .annotate(
            total_quantity = Sum('remaining')
        )
        .order_by('price')
    )
    return {
        'bids' : list(buy_book),
        'asks' : list(sell_book),
    }

