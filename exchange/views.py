from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db.models import Q
from django.contrib.auth.models import User
import logging

from .services.exchange_service import place_order, cancel_order

logger = logging.getLogger(__name__)
from .services.orderbook import get_order_book
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    PortfolioSerializer,
    HoldingSerializer,
    TradeSerializer,
)
from .models import Order, Portfolio, Holding, Trade, Symbol
from .channel_events import broadcast_orderbook
from .services.market_data import fetch_candles


class HealthCheckView(APIView):
    """Health check endpoint for monitoring."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"status": "ok", "service": "mini-exchange-api"},
            status=status.HTTP_200_OK
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password")

        if not username:
            return Response(
                {"detail": "Username is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not password:
            return Response(
                {"detail": "Password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {"detail": "A user with that username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User.objects.create_user(username=username, password=password)
        return Response(
            {"detail": "Account created. You can sign in now."},
            status=status.HTTP_201_CREATED,
        )


class PortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Use get_or_create to ensure portfolio exists
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
        return Response(PortfolioSerializer(portfolio).data)


class HoldingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        holdings = Holding.objects.filter(user=request.user).select_related('symbol')
        return Response(HoldingSerializer(holdings, many=True).data)


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Order.objects.filter(user=request.user).select_related('symbol').order_by('-created_at')
        status_param = request.query_params.get('status')
        if status_param:
            statuses = [s.strip() for s in status_param.split(',') if s.strip()]
            if statuses:
                qs = qs.filter(status__in=statuses)
        symbol_param = request.query_params.get('symbol')
        if symbol_param:
            qs = qs.filter(symbol__name=symbol_param)
        return Response(OrderSerializer(qs, many=True).data)

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        symbol_name = serializer.validated_data['symbol']
        
        try:
            order = place_order(
                user=request.user,
                symbol_name=symbol_name,
                side=serializer.validated_data['side'],
                price=serializer.validated_data['price'],
                quantity=serializer.validated_data['quantity'],
            )
            broadcast_orderbook(symbol_name)
            return Response(OrderSerializer(order).data, status=201)
        except ValueError as e:
            logger.warning(f"Order placement failed for user {request.user}: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Unexpected error placing order: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred while placing the order."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = cancel_order(request.user, order_id)
        broadcast_orderbook(order.symbol.name)
        return Response(OrderSerializer(order).data, status=200)


class OrderBookView(APIView):
    permission_classes = []

    def get(self, request):
        from .models import Symbol

        symbol_param = request.query_params.get('symbol')
        if not symbol_param or not str(symbol_param).strip():
            return Response(
                {'detail': 'Missing or invalid symbol.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        symbol = Symbol.get_by_name(symbol_param)
        if symbol is None:
            return Response(
                {'detail': 'Symbol not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        order_book = get_order_book(symbol)
        return Response(order_book)


class TradeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Trade.objects.filter(
            Q(buy_order__user=user) | Q(sell_order__user=user)
        ).select_related('buy_order', 'sell_order', 'buy_order__symbol', 'sell_order__symbol').order_by('-created_at')
        symbol_param = request.query_params.get('symbol')
        if symbol_param:
            qs = qs.filter(buy_order__symbol__name=symbol_param)
        out = []
        for t in qs:
            if t.buy_order.user_id == user.id:
                side = 'BUY'
                symbol_name = t.buy_order.symbol.name
            else:
                side = 'SELL'
                symbol_name = t.sell_order.symbol.name
            out.append({
                'id': t.id,
                'symbol': symbol_name,
                'side': side,
                'price': str(t.price),
                'quantity': t.quantity,
                'created_at': t.created_at,
            })
        return Response(out)


class SymbolListView(APIView):
    permission_classes = []

    def get(self, request):
        qs = Symbol.objects.all().order_by('name')
        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        names = list(qs.values_list('name', flat=True)[:50])
        return Response(names)


class PricesView(APIView):
    """Delayed market prices for all symbols. Refreshed at most every 60 minutes."""
    permission_classes = []

    def get(self, request):
        from .services.price_fetch import update_symbol_prices
        update_symbol_prices(cache_minutes=60)
        qs = Symbol.objects.all().order_by('name')
        out = []
        for s in qs:
            out.append({
                'symbol': s.name,
                'price': float(s.last_price) if s.last_price is not None else None,
                'updated_at': s.last_price_updated_at.isoformat() if s.last_price_updated_at else None,
            })
        return Response(out)
    
class CandleView(APIView):
    permission_classes = []

    def get(self, request):
        symbol = request.query_params.get("symbol")

        if not symbol:
            return Response({"detail": "Symbol required."}, status=400)

        candles = fetch_candles(symbol)
        return Response(candles)