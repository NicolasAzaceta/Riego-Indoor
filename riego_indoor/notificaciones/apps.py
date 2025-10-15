from django.apps import AppConfig

class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notificaciones'

    def ready(self):      
         # importar signals para que queden registrados      
         import notificaciones.signals  # noqa