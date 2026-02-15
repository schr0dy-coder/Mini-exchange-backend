import requests
from django.conf import settings
from django.core.cache import cache
BASE_URL = "https://api.twelvedata.com/time_series"

def fetch_candles(symbol, interval="1min", outputsize=50):
    cache_key = f"candles_{symbol}_{interval}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": settings.TWELVE_DATA_API_KEY,
    }

    response = requests.get(BASE_URL, params=params, timeout=5)
    data = response.json()

    if "values" not in data:
        return []

    candles = [
        {
            "time": row["datetime"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
        }
        for row in reversed(data["values"])
    ]

    cache.set(cache_key, candles, 60)  # cache for 60 sec
    return candles
