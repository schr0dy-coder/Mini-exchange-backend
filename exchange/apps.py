from django.apps import AppConfig
from threading import Thread

class ExchangeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exchange'

    def ready(self):
        from .services.market_simulator import simulation_loop
        thread = Thread(target=simulation_loop)
        thread.daemon = True
        thread.start()