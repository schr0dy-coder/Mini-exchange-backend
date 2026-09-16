from django.apps import AppConfig
from threading import Thread

class ExchangeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exchange'

    def ready(self):
        import exchange.signals
        from .services.market_simulator import simulation_loop
        from .services.auto_prober import start_auto_prober

        thread = Thread(target=simulation_loop)
        thread.daemon = True
        thread.start()

        start_auto_prober()