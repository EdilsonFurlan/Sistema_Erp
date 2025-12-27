from django.apps import AppConfig


class MoldsConfig(AppConfig):
    name = 'molds'

    def ready(self):
        import molds.signals
