from django.urls import path
from .views import (
    HealthCheckView,
    CandleView,
    OrderListCreateView,
    CancelOrderView,
    OrderBookView,
    PortfolioView,
    HoldingsView,
    TradeListView,
    SymbolListView,
    RegisterView,
    PricesView, 
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('register/', RegisterView.as_view(), name='register'),
    path('symbols/', SymbolListView.as_view(), name='symbol_list'),
    path('prices/', PricesView.as_view(), name='prices'),
    path('portfolio/', PortfolioView.as_view(), name='portfolio'),
    path('holdings/', HoldingsView.as_view(), name='holdings'),
    path('orders/', OrderListCreateView.as_view(), name='order_list_create'),
    path('orders/<int:order_id>/cancel/', CancelOrderView.as_view(), name='cancel_order'),
    path('orderbook/', OrderBookView.as_view(), name='order_book'),
    path('trades/', TradeListView.as_view(), name='trade_list'),
    path('candles/', CandleView.as_view(), name='candles'),
]
