# filepath: c:\Users\LucaRodriguez\Desktop\Riego-Indoor\riego_indoor\notificaciones\signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from plantas.models import Riego, Planta
from .services.google_calendar import get_user_calendar_service
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
    - Si ya existe un evento, lo elimina.
    - Crea un nuevo evento con la fecha actualizada.
    - Guarda el ID del nuevo evento en la planta.
    """
    user = planta.usuario
    
    # 1. Verificar si el usuario ha vinculado su cuenta de Google
    if not hasattr(user, 'profile') or not user.profile.google_access_token:
        print(f"Usuario {user.username} no ha vinculado Google Calendar. No se crea evento.")
        return

    service = get_user_calendar_service(user)

    # 2. Si ya existe un evento, lo eliminamos primero.
    if planta.google_calendar_event_id:
        try:
            service.events().delete(calendarId='primary', eventId=planta.google_calendar_event_id).execute()
            print(f"Evento anterior '{planta.google_calendar_event_id}' eliminado para la planta '{planta.nombre_personalizado}'.")
        except Exception as e:
            # Si el evento no se encuentra (ej: borrado manualmente por el usuario), no es un error crítico.
            print(f"No se pudo eliminar el evento anterior '{planta.google_calendar_event_id}': {e}")

    # 3. Obtener los cálculos de riego para saber la próxima fecha
    calculos = planta.calculos_riego()
    next_watering_date = calculos.get('next_watering_date')

    if not next_watering_date:
        print(f"No se pudo calcular la próxima fecha de riego para {planta.nombre_personalizado}.")
        return

    # 4. Preparar los datos del nuevo evento

    # Hora del evento (ej: 9:00 AM). Se puede hacer configurable por usuario en el futuro.
    event_time = time(9, 0)
    start_datetime = datetime.combine(next_watering_date, event_time)
    end_datetime = start_datetime + timedelta(minutes=30)

    event = {
        'summary': f'💧 Regar: {planta.nombre_personalizado}',
        'description': (
            f'¡Es hora de regar tu planta "{planta.nombre_personalizado}"!\n\n'
            f'💧 Cantidad de agua recomendada: {calculos["recommended_water_ml"]} ml.\n'
            f'🪴 Tipo de planta: {planta.tipo_planta}.'
        ),
        'start': {'dateTime': start_datetime.isoformat(), 'timeZone': settings.TIME_ZONE},
        'end': {'dateTime': end_datetime.isoformat(), 'timeZone': settings.TIME_ZONE},
        'colorId': '9',  # 9 = Azul "Blueberry"
        'reminders': {'useDefault': True},  # Usa las notificaciones por defecto del usuario
    }

    # 5. Insertar el evento y guardar su ID
    try:
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        # Usamos update() en lugar de save() para evitar un ciclo de señales post_save.
        Planta.objects.filter(pk=planta.pk).update(google_calendar_event_id=created_event['id'])
        # Actualizamos el objeto en memoria para que tenga el ID correcto si se usa después.
        planta.refresh_from_db()
        print(f"Evento de riego creado/actualizado para '{planta.nombre_personalizado}' el {next_watering_date}. ID: {created_event['id']}")
    except Exception as e:
        print(f"Error al crear el evento de Google Calendar para '{planta.nombre_personalizado}': {e}")
        # Nos aseguramos de que no quede un ID viejo si la creación falla
        Planta.objects.filter(pk=planta.pk).update(google_calendar_event_id=None)
        planta.refresh_from_db()

@receiver(post_save, sender=Planta)
def update_event_on_planta_save(sender, instance, created, **kwargs):
    """
    Cuando se crea o actualiza una planta, se crea/actualiza el evento
    del calendario para el próximo riego.
    - `created=True`: Se ejecuta al crear una nueva planta.
    - `created=False`: Se ejecuta al modificar una planta existente.
    """
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
