"""
Fetch delayed stock prices from a free source and cache in DB.
Uses yfinance (Yahoo Finance) – no API key; data is delayed to stay within free use.
"""
from decimal import Decimal
from django.utils import timezone


def update_symbol_prices(cache_minutes=60):
    """
    Update last_price for all Symbol records if cache is older than cache_minutes.
    Returns number of symbols updated.
    """
    try:
        import yfinance as yf
    except ImportError:
        return 0

    from exchange.models import Symbol
    from datetime import timedelta

    threshold = timezone.now() - timedelta(minutes=cache_minutes)
    symbols = list(Symbol.objects.all())
    updated = 0
    for sym in symbols:
        if sym.last_price_updated_at and sym.last_price_updated_at >= threshold:
            continue
        try:
            ticker = yf.Ticker(sym.name)
            info = ticker.info
            price = info.get("regularMarketPrice") or info.get("previousClose") or info.get("open")
            if price is not None:
                sym.last_price = Decimal(str(round(float(price), 2)))
                sym.last_price_updated_at = timezone.now()
                sym.save(update_fields=["last_price", "last_price_updated_at"])
                updated += 1
        except Exception:
            continue
    return updated


def fetch_symbol_price(symbol_name):
    """Fetch latest price for a single symbol and update the DB record.

    Returns Decimal price or None.
    """
    try:
        import yfinance as yf
    except ImportError:
        return None

    from exchange.models import Symbol
    try:
        sym = Symbol.objects.filter(name__iexact=str(symbol_name).strip()).first()
        if not sym:
            return None
        ticker = yf.Ticker(sym.name)
        info = ticker.info
        price = info.get("regularMarketPrice") or info.get("previousClose") or info.get("open")
        if price is not None:
            from decimal import Decimal
            from django.utils import timezone

            sym.last_price = Decimal(str(round(float(price), 2)))
            sym.last_price_updated_at = timezone.now()
            sym.save(update_fields=["last_price", "last_price_updated_at"])
            return sym.last_price
    except Exception:
        return None
    return None
