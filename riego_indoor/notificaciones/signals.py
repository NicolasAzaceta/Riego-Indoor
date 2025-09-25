# notificaciones/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_profile_for_user(sender, instance, created, **kwargs):
    """
    Crea un Profile al crear el User y, si el user tiene email, lo setea en calendar_id
    (solo si calendar_id está vacío, para no sobreescribir si luego el user lo cambia).
    """
    if created:
        Profile.objects.create(user=instance, calendar_id=(instance.email or '').strip() or None)
    else:
        # si existe pero no tiene calendar_id y el user tiene email, lo completamos
        try:
            profile = instance.profile
            if not profile.calendar_id and instance.email:
                profile.calendar_id = instance.email.strip()
                profile.save(update_fields=['calendar_id'])
        except Profile.DoesNotExist:
            # por si no existiera por cualquier razón, lo creamos
            Profile.objects.create(user=instance, calendar_id=(instance.email or '').strip() or None)












# # notificaciones/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth import get_user_model
# from django.db import transaction
# from datetime import timedelta
# from django.utils import timezone

# from .models import Profile  # si Profile está en notificaciones.models
# # Si Profile está en otra app, importalo desde esa app: from users.models import Profile
# from plantas.models import Riego, Planta  # ajustá 'riego_app' al nombre real de tu app de riego
# from .services.google_calendar import (
#     ensure_timezone,
#     create_calendar_event,
#     DEFAULT_TZ,
# )

# User = get_user_model()

# # 1) Signal para crear/actualizar Profile cuando se crea un User
# @receiver(post_save, sender=User)
# def create_or_update_profile_for_user(sender, instance, created, **kwargs):
#     """
#     Cuando se crea un User, aseguramos que exista Profile y,
#     si el User tiene email, lo usamos como calendar_id por defecto.
#     """
#     # Evitamos errores si Profile está en otra app
#     try:
#         profile, _ = Profile.objects.get_or_create(user=instance)
#         if instance.email:
#             # Sólo seteamos si no existe calendar_id (para no sobreescribir)
#             if not profile.calendar_id:
#                 profile.calendar_id = instance.email.strip()
#                 profile.save(update_fields=['calendar_id'])
#     except Exception as e:
#         # No queremos romper la creación de usuarios si algo falla:
#         # loguear en consola para debug
#         print(f"[notificaciones] create_or_update_profile_for_user error: {e}")


# # 2) Signal para reaccionar cuando se crea un Riego
# @receiver(post_save, sender=Riego)
# def on_riego_created(sender, instance: Riego, created, **kwargs):
#     """
#     - Actualiza Planta.fecha_ultimo_riego con la fecha del Riego.
#     - Calcula proximo riego (usando planta.calculos_riego()).
#     - Si existe calendar_id para el owner, crea un evento en Google Calendar.
#     """
#     if not created:
#         # Sólo actuamos en creación, no en updates
#         return

#     planta = instance.planta
#     if planta is None:
#         return

#     # 1) Actualizar fecha_ultimo_riego en Planta (no interferimos con serializers existentes)
#     try:
#         planta.fecha_ultimo_riego = instance.fecha
#         planta.save(update_fields=['fecha_ultimo_riego'])
#     except Exception as e:
#         print(f"[notificaciones] Error guardando fecha_ultimo_riego: {e}")

#     # 2) Obtener calendar_id (Profile.calendar_id preferido; fallback a owner.email)
#     calendar_id = None
#     owner = getattr(planta, 'usuario', None) or getattr(planta, 'owner', None) or None
#     if owner:
#         profile = getattr(owner, 'profile', None)
#         if profile and getattr(profile, 'calendar_id', None):
#             calendar_id = profile.calendar_id
#         elif getattr(owner, 'email', None):
#             calendar_id = owner.email

#     # 3) Calcular próxima fecha de riego con la función existente de Planta
#     next_dt = None
#     try:
#         calc = planta.calculos_riego()
#         next_dt = calc.get('next_watering_date') or calc.get('next_riego') or None
#     except Exception as e:
#         print(f"[notificaciones] Error calculando próximo riego: {e}")
#         next_dt = None

#     # 4) Si tenemos calendar_id y next_dt, crear evento en Google Calendar
#     if calendar_id and next_dt:
#         try:
#             start_dt = ensure_timezone(next_dt, DEFAULT_TZ)
#             end_dt = start_dt + timedelta(minutes=20)  # duración por defecto
#             summary = f"Recordatorio de riego: {planta.nombre_personalizado or planta.nombre or 'Planta'}"
#             description = (
#                 f"Recordatorio automático generado por Riego Indoor.\n"
#                 f"Planta: {planta.nombre_personalizado or planta.nombre}\n"
#                 f"Último riego: {instance.fecha}\n"
#                 f"Cantidad anterior: {instance.cantidad_agua_ml} ml"
#             )

#             event = create_calendar_event(
#                 calendar_id=calendar_id,
#                 summary=summary,
#                 start_dt=start_dt,
#                 end_dt=end_dt,
#                 description=description,
#             )
#             print(f"[notificaciones] Evento creado en Google Calendar: {event.get('htmlLink')}")

#         except Exception as e:
#             # No rompemos la creación del riego por un fallo externo
#             print(f"[notificaciones] Error creando evento en Google Calendar: {e}")
