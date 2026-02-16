from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Portfolio
from decimal import Decimal

@receiver(post_save, sender=User)
def create_portfolio(sender, instance, created, **kwargs):
    if created:
        Portfolio.objects.create(
            user=instance,
            available_balance=Decimal("10000000"),   # starting capital
            reserved_balance=Decimal("0"),
        )

@receiver(post_save, sender=User)
def save_user_portfolio(sender, instance, **kwargs):
    # Ensure portfolio exists and save it
    portfolio, _ = Portfolio.objects.get_or_create(user=instance)
    portfolio.save()
