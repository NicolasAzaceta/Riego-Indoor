from django.apps import AppConfig


class PlantasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plantas'

    def ready(self):
        """
        Called when Django starts.
        
        NOTA: APScheduler deshabilitado - ahora usamos Render Cron Jobs.
        El scheduler solo está disponible para testing local si es necesario.
        """
        # Registrar signals de imágenes
        import plantas.signals_images
        
        # APScheduler deshabilitado en favor de Render Cron Jobs
        # Si necesitas usarlo localmente, descomentá las siguientes líneas:
        
        # import os
        # if os.environ.get('RUN_MAIN') != 'true':
        #     from plantas.scheduler import start_scheduler
        #     start_scheduler()
