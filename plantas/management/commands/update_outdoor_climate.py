"""
Management command para actualizar el clima outdoor y recalcular riegos.

Este comando se ejecuta diariamente via Render Cron Job.

Uso:
    python manage.py update_outdoor_climate
    
    # Con verbose output
    python manage.py update_outdoor_climate --verbose
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from plantas.models import LocalidadUsuario, Planta
from plantas.services.weather_service import obtener_y_guardar_clima
from plantas.services.outdoor_calculator import recalcular_fecha_riego_outdoor
from notificaciones.services.google_calendar import update_calendar_event_for_plant
from datetime import datetime


class Command(BaseCommand):
    help = 'Actualiza el clima outdoor para todas las localidades activas y recalcula riegos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra output detallado de la ejecución',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        start_time = datetime.now()
        self.stdout.write(self.style.SUCCESS(f'\n🌤️  Iniciando actualización de clima outdoor - {start_time.strftime("%Y-%m-%d %H:%M:%S")}'))
        
        # === PASO 1: Obtener todas las localidades activas ===
        localidades_activas = LocalidadUsuario.objects.filter(activo=True)
        
        if not localidades_activas.exists():
            self.stdout.write(self.style.WARNING('⚠️  No hay localidades outdoor activas configuradas'))
            return
        
        self.stdout.write(f'\n📍 Encontradas {localidades_activas.count()} localidades activas')
        
        localidades_procesadas = 0
        localidades_error = 0
        plantas_actualizadas = 0
        
        # === PASO 2: Procesar cada localidad ===
        for localidad in localidades_activas:
            try:
                if verbose:
                    self.stdout.write(f'\n  → Procesando: {localidad.nombre_localidad}')
                
                # Obtener y guardar clima actual
                registro_clima = obtener_y_guardar_clima(localidad)
                
                if not registro_clima:
                    self.stdout.write(self.style.ERROR(f'    ✗ Error al obtener clima para {localidad.nombre_localidad}'))
                    localidades_error += 1
                    continue
                
                if verbose:
                    self.stdout.write(f'    ✓ Clima actualizado: {registro_clima.temperatura_max}°C, {registro_clima.precipitacion_mm}mm lluvia')
                
                localidades_procesadas += 1
                
                # === PASO 3: Recalcular riegos para plantas outdoor de este usuario ===
                plantas_outdoor = Planta.objects.filter(
                    usuario=localidad.user,
                    tipo_cultivo='outdoor'
                )
                
                for planta in plantas_outdoor:
                    try:
                        # Recalcular fecha de riego basándose en el clima
                        resultado = recalcular_fecha_riego_outdoor(planta, registro_clima)
                        
                        if verbose:
                            self.stdout.write(f'    ✓ Planta "{planta.nombre_personalizado}": {resultado["dias_restantes"]} días hasta riego')
                            if resultado.get('reseteo_por_lluvia'):
                                self.stdout.write(f'      🌧️  Riego reseteado por lluvia intensa')
                        
                        # === PASO 4: Actualizar Google Calendar si está vinculado ===
                        if planta.google_calendar_event_id:
                            try:
                                update_calendar_event_for_plant(planta)
                                if verbose:
                                    self.stdout.write(f'      📅 Google Calendar actualizado')
                            except Exception as e:
                                if verbose:
                                    self.stdout.write(self.style.WARNING(f'      ⚠️  No se pudo actualizar Calendar: {str(e)}'))
                        
                        plantas_actualizadas += 1
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    ✗ Error al recalcular planta "{planta.nombre_personalizado}": {str(e)}'))
                        continue
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error al procesar localidad: {str(e)}'))
                localidades_error += 1
                continue
        
        # === RESUMEN FINAL ===
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Actualización completada en {duration:.2f} segundos'))
        self.stdout.write(f'\n📊 Resumen:')
        self.stdout.write(f'   • Localidades procesadas: {localidades_procesadas}/{localidades_activas.count()}')
        self.stdout.write(f'   • Plantas actualizadas: {plantas_actualizadas}')
        if localidades_error > 0:
            self.stdout.write(self.style.WARNING(f'   • Errores: {localidades_error}'))
        self.stdout.write('')
