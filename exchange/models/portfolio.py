from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    available_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("100000.00")
        )
    reserved_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00")
        )



    def __str__(self):
        return f"{self.user.username}'s Portfolio"