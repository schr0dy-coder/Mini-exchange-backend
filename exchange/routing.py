from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/orderbook/$", consumers.OrderBookConsumer.as_asgi()),
    re_path(r"ws/prices/$", consumers.PricesConsumer.as_asgi()),
    re_path(r"ws/prices/$", consumers.PricesConsumer.as_asgi()),
]
