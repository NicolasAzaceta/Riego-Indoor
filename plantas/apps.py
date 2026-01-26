from django.apps import AppConfig


class PlantasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plantas'

    def ready(self):
        """
        Called when Django starts.
        Inicia el scheduler de riegos outdoor automáticos.
        """
        # Solo iniciar scheduler en proceso principal (no en reloader)
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            # Esto solo se ejecuta una vez, no en cada reload del dev server
            from plantas.scheduler import start_scheduler
            start_scheduler()
