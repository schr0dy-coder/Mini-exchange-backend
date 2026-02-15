from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .symbol import Symbol
class Order(models.Model):
    class Side(models.TextChoices):
        BUY = 'BUY', 'Buy'
        SELL = 'SELL', 'Sell'
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        PARTIAL = 'PARTIAL', 'Partial'
        FILLED = 'FILLED', 'Filled'
        CANCELED = 'CANCELED', 'Canceled'
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    side = models.CharField(max_length=4, choices=Side.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    symbol = models.ForeignKey(
        Symbol, on_delete=models.CASCADE, 
        related_name='orders'
        )

    quantity = models.PositiveIntegerField()
    filled_quantity = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['side', 'status', 'price', 'created_at']),
        ]
    @property
    def remaining_quantity(self):
        return self.quantity - self.filled_quantity
    def clean(self):
        if self.filled_quantity > self.quantity:
            raise ValidationError("Filled quantity cannot exceed total quantity.")
        if self.filled_quantity  == self.quantity and self.status != 'FILLED':
            raise ValidationError("Status must be 'FILLED' when filled quantity equals total quantity.")
    