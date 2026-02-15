from rest_framework import serializers
from decimal import Decimal
from .models import Order, Portfolio, Holding, Trade


class OrderCreateSerializer(serializers.Serializer):
    side = serializers.ChoiceField(choices=Order.Side.choices)
    symbol = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_price(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'side',
            'price',
            'quantity',
            'filled_quantity',
            'remaining_quantity',
            'status',
            'created_at',
            'symbol_name',
        ]
        read_only_fields = fields


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['available_balance', 'reserved_balance']


class HoldingSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = Holding
        fields = ['symbol', 'available_quantity', 'reserved_quantity']


class TradeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    symbol = serializers.CharField()
    side = serializers.ChoiceField(choices=Order.Side.choices)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField()
    created_at = serializers.DateTimeField()
