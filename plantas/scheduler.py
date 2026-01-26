"""
Scheduler para recálculo automático de riegos outdoor basado en clima.

Este scheduler se ejecuta diariamente a las 3:00 AM UTC y:
1. Obtiene el clima de cada localidad activa
2. Guarda registro en RegistroClima
3. Recalcula riegos de plantas outdoor
4. Actualiza eventos en Google Calendar
"""

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.contrib.auth.models import User
from datetime import date
import logging

logger = logging.getLogger(__name__)


def recalcular_riegos_outdoor_diario():
    """
    Task que se ejecuta diariamente para recalcular riegos outdoor.
    
    Este es el corazón del sistema automático:
    - Consulta el clima para cada localidad activa
    - Guarda registro del clima
    - Recalcula el próximo riego para plantas outdoor
    - Actualiza Google Calendar con nuevas fechas
    """
    from plantas.models import LocalidadUsuario, Planta
    from plantas.services.weather_service import obtener_y_guardar_clima
    from plantas.services.outdoor_calculator import recalcular_fecha_riego_outdoor
    from notificaciones.services.google_calendar import actualizar_evento_riego
    
    logger.info("🌤️ Iniciando recálculo diario de riegos outdoor...")
    
    # Obtener todas las localidades activas
    localidades = LocalidadUsuario.objects.filter(activo=True).select_related('user')
    
    if not localidades.exists():
        logger.info("No hay localidades activas para procesar")
        return
    
    total_plantas_procesadas = 0
    total_errores = 0
    
    for localidad in localidades:
        try:
            # 1. Obtener y guardar clima
            logger.info(f"Consultando clima para {localidad.nombre_localidad}...")
            registro_clima = obtener_y_guardar_clima(localidad)
            
            if registro_clima is None:
                logger.warning(f"No se pudo obtener clima para {localidad.nombre_localidad}")
                total_errores += 1
                continue
            
            # 2. Obtener plantas outdoor del usuario
            plantas_outdoor = Planta.objects.filter(
                usuario=localidad.user,
                tipo_cultivo='outdoor'
            )
            
            logger.info(f"Procesando {plantas_outdoor.count()} plantas outdoor de {localidad.user.username}...")
            
            for planta in plantas_outdoor:
                try:
                    # 3. Recalcular riego
                    resultado = recalcular_fecha_riego_outdoor(planta, registro_clima)
                    
                    # 4. Actualizar Google Calendar
                    if hasattr(localidad.user, 'profile') and localidad.user.profile.google_access_token:
                        try:
                            from notificaciones.services.google_calendar import delete_calendar_event, create_riego_event
                            
                            # Borrar evento anterior si existe
                            if planta.google_calendar_event_id:
                                delete_calendar_event(localidad.user, planta.google_calendar_event_id)
                            
                            # Crear nuevo evento con fecha actualizada
                            nuevo_evento = create_riego_event(
                                user=localidad.user,
                                planta=planta,
                                fecha_riego=resultado['fecha_proximo_riego'],
                                motivo=resultado['motivo']
                            )
                            
                            if nuevo_evento:
                                planta.google_calendar_event_id = nuevo_evento.get('id')
                                planta.save(update_fields=['google_calendar_event_id'])
                        
                        except Exception as e:
                            logger.error(f"Error al actualizar Google Calendar para {planta.nombre_personalizado}: {e}")
                    
                    total_plantas_procesadas += 1
                    logger.debug(f"✅ {planta.nombre_personalizado}: {resultado['motivo']}")
                
                except Exception as e:
                    logger.error(f"Error procesando planta {planta.nombre_personalizado}: {e}")
                    total_errores += 1
            
            # Marcar registro como procesado
            registro_clima.riegos_recalculados = True
            registro_clima.save()
        
        except Exception as e:
            logger.error(f"Error procesando localidad {localidad.nombre_localidad}: {e}")
            total_errores += 1
    
    logger.info(f"✅ Recálculo completado: {total_plantas_procesadas} plantas procesadas, {total_errores} errores")


def procesar_dias_faltantes():
    """
    Procesa días faltantes cuando el servidor se reinicia.
    
    Si el servidor estuvo inactivo por varios días (ej: Render lo suspendió),
    este método procesa el clima de los días que se perdieron.
    """
    from plantas.models import LocalidadUsuario, RegistroClima
    from datetime import timedelta
    
    logger.info("Verificando días faltantes...")
    
    localidades = LocalidadUsuario.objects.filter(activo=True)
    
    for localidad in localidades:
        # Verificar si hay registros recientes
        ultimo_registro = RegistroClima.objects.filter(
            localidad=localidad
        ).order_by('-fecha').first()
        
        if ultimo_registro:
            dias_desde_ultimo = (date.today() - ultimo_registro.fecha).days
            
            if dias_desde_ultimo > 1:
                logger.warning(f"Faltan {dias_desde_ultimo - 1} días de clima para {localidad.nombre_localidad}")
                # Por ahora solo loggeamos, en el futuro podríamos usar historical weather API


# Instancia global del scheduler
scheduler = None


def start_scheduler():
    """
    Inicia el scheduler de tareas automáticas.
    
    Solo se ejecuta en producción (DEBUG=False) para evitar
    ejecuciones duplicadas durante desarrollo.
    """
    global scheduler
    
    # Solo en producción
    if settings.DEBUG:
        logger.info("⏭️ Scheduler deshabilitado en modo DEBUG")
        return
    
    if scheduler is not None:
        logger.warning("Scheduler ya está corriendo")
        return
    
    logger.info("🚀 Iniciando scheduler de riegos outdoor...")
    
    scheduler = BackgroundScheduler()
    
    # Task diario a las 3:00 AM UTC
    scheduler.add_job(
        recalcular_riegos_outdoor_diario,
        'cron',
        hour=3,
        minute=0,
        id='outdoor_irrigation_recalc',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler iniciado - Recálculo diario a las 3:00 AM UTC")
    
    # Procesar días faltantes al iniciar
    procesar_dias_faltantes()


def stop_scheduler():
    """
    Detiene el scheduler (útil para testing y shutdown).
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("⏹️ Scheduler detenido")
