from django.db import models
from decimal import Decimal


class Symbol(models.Model):
    name = models.CharField(max_length=100, unique=True)
    last_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Last fetched market price (delayed, for display only).",
    )
    last_price_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name):
        """Resolve symbol by name (case-insensitive, stripped). Returns Symbol or None."""
        if not name or not str(name).strip():
            return None
        return cls.objects.filter(name__iexact=str(name).strip()).first()