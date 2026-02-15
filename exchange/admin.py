from django.contrib import admin
from .models import Order, Trade, Portfolio, Symbol, Holding

# Register your models here.    

admin.site.register(Order)
admin.site.register(Trade)
admin.site.register(Portfolio)
admin.site.register(Symbol)
admin.site.register(Holding)