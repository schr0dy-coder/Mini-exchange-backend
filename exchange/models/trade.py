from django.db import models
from .order import Order

class Trade(models.Model):

    buy_order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='buy_trades',
        )
    
    sell_order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='sell_trades',
        )
    
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2
    )
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)