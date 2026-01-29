# filepath: c:\Users\LucaRodriguez\Desktop\Riego-Indoor\riego_indoor\notificaciones\signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from plantas.models import Riego, Planta
from .services.google_calendar import get_user_calendar_service, update_calendar_event_for_plant
from django.contrib.auth.models import User
from .models import Profile
from django.conf import settings
from datetime import timedelta, datetime, time

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance, defaults={'calendar_id': instance.email})

def _update_or_create_next_watering_event(planta):
    """
    Función helper para crear o actualizar el evento del próximo riego.
    Delegamos toda la lógica al servicio centralizado para mantener consistencia.
    """
    user = planta.usuario
    
    # 1. Verificar si el usuario ha vinculado su cuenta de Google
    if not hasattr(user, 'profile') or not user.profile.google_access_token:
        # print(f"Usuario {user.username} no ha vinculado Google Calendar. No se crea evento.")
        return

    try:
        # Usamos la función centralizada que maneja:
        # - Recálculo de fechas
        # - Borrado de eventos anteriores
        # - Creación del nuevo evento con estilo unificado
        # - Guardado del ID en la base de datos
        update_calendar_event_for_plant(planta)
        
    except Exception as e:
        print(f"Error en señal de actualización de calendario para '{planta.nombre_personalizado}': {e}")

@receiver(post_save, sender=Planta)
def update_event_on_planta_save(sender, instance, created, **kwargs):
    """
    Cuando se crea o actualiza una planta, se crea/actualiza el evento
    del calendario para el próximo riego.
    - `created=True`: Se ejecuta al crear una nueva planta.
    - `created=False`: Se ejecuta al modificar una planta existente.
    """
    # Evitar recursión infinita o reacciones a actualizaciones internas:
    # Si la actualización es SOLO del campo google_calendar_event_id, no hacemos nada.
    if kwargs.get('update_fields') and 'google_calendar_event_id' in kwargs['update_fields']:
        return

    _update_or_create_next_watering_event(instance)

@receiver(post_save, sender=Riego)
def create_event_on_riego_save(sender, instance, created, **kwargs):
    """
    Cuando se registra un nuevo riego, se actualiza el evento
    del calendario a la siguiente fecha de riego calculada.
    """
    if created:
        _update_or_create_next_watering_event(instance.planta)

@receiver(post_delete, sender=Planta)
def delete_event_on_planta_delete(sender, instance, **kwargs):
    """
    Cuando se elimina una planta, también se elimina su evento
    asociado del Google Calendar.
    """
    planta = instance
    user = planta.usuario

    # 1. Verificar si hay un evento para eliminar y si el usuario tiene el calendario vinculado.
    if not planta.google_calendar_event_id:
        return

    if not hasattr(user, 'profile') or not user.profile.google_access_token:
        return

    # 2. Intentar eliminar el evento del calendario.
    try:
        service = get_user_calendar_service(user)
        service.events().delete(calendarId='primary', eventId=planta.google_calendar_event_id).execute()
        print(f"Evento '{planta.google_calendar_event_id}' eliminado del calendario para la planta '{planta.nombre_personalizado}' que fue borrada.")
    except Exception as e:
        # Si el evento ya no existe en Google Calendar, no es un error crítico.
        print(f"No se pudo eliminar el evento '{planta.google_calendar_event_id}' del calendario (puede que ya haya sido borrado): {e}")
