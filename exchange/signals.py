from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Portfolio, Holding, Symbol
from decimal import Decimal

@receiver(post_save, sender=User)
def create_portfolio(sender, instance, created, **kwargs):
    if created:
        Portfolio.objects.create(
            user=instance,
            available_balance=Decimal("100000"),   # starting capital
            reserved_balance=Decimal("0"),
        )
        
        # Seed holdings: give new user 10,000 shares of each symbol
        symbols = Symbol.objects.all()
        for symbol in symbols:
            Holding.objects.get_or_create(
                user=instance,
                symbol=symbol,
                defaults={
                    "available_quantity": 10000,
                    "reserved_quantity": 0,
                }
            )

@receiver(post_save, sender=User)
def save_user_portfolio(sender, instance, **kwargs):
    # Ensure portfolio exists and save it
    portfolio, _ = Portfolio.objects.get_or_create(user=instance)
    portfolio.save()
