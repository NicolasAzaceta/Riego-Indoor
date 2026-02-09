from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from .models import Planta, Riego, ConfiguracionUsuario, LocalidadUsuario, RegistroClima, AuditLog, ImagenPlanta
from .serializers import PlantaSerializer, RiegoSerializer, RegisterSerializer, ConfiguracionUsuarioSerializer, LocalidadUsuarioSerializer
from .permissions import IsOwner
from .storage_service import PlantImageStorageService
from .serializers import ImagenPlantaSerializer
from notificaciones.services.google_calendar import get_user_calendar_service

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, Max, Min, Value
from django.db.models.functions import Coalesce
from django.contrib.auth import login, authenticate
from django.conf import settings
import requests

# Logger para este módulo
logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'home.html')

def index_view(request):
    return render(request, 'index.html', {'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY})

def add_view(request):
    return render(request, 'add-plants.html')

def detail_view(request):
    return render(request, 'detail.html')

def login_view(request):
    return render(request, 'login.html')

def register_view(request):
    return render(request, 'register.html')

def privacy_view(request):
    return render(request, 'privacy.html')

def terms_view(request):
    return render(request, 'terms.html')

# -------- Registro de usuarios --------
from rest_framework.views import APIView

class RegisterView(APIView):
    permission_classes = []  # cualquiera puede registrarse
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Registrar auditoría
        AuditLog.log(user, 'REGISTER', request, details={'email': user.email})
        logger.info(f"Nuevo usuario registrado: {user.username}")
        
        return Response({"id": user.id, "username": user.username}, status=status.HTTP_201_CREATED)

class ConfiguracionUsuarioView(APIView):
    """
    GET: Obtener configuración indoor del usuario
    PATCH: Actualizar temperatura y/o humedad indoor
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Obtener o crear configuración del usuario
        config, created = ConfiguracionUsuario.objects.get_or_create(user=request.user)
        serializer = ConfiguracionUsuarioSerializer(config)
        return Response(serializer.data)
    
    def patch(self, request):
        # Actualizar configuración indoor
        config, created = ConfiguracionUsuario.objects.get_or_create(user=request.user)
        serializer = ConfiguracionUsuarioSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class LocalidadUsuarioView(APIView):
    """
    GET: Obtener localidad outdoor del usuario
    POST: Crear/actualizar localidad outdoor
    DELETE: Eliminar localidad outdoor
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            localidad = request.user.localidad_outdoor
            serializer = LocalidadUsuarioSerializer(localidad)
            return Response(serializer.data)
        except LocalidadUsuario.DoesNotExist:
            # Retornar objeto vacío en lugar de 404 - permite que el frontend funcione sin errores
            return Response({}, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        Guardar/actualizar localidad outdoor.
        Espera: { "nombre_localidad": "Córdoba, Argentina" }
        Hace geocoding en backend para mayor seguridad.
        """
        nombre_localidad = request.data.get('nombre_localidad', '').strip()
        
        if not nombre_localidad:
            return Response(
                {"error": "El nombre de la localidad es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Geocoding usando Google Maps API (en backend)
        try:
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': nombre_localidad,
                'key': settings.GOOGLE_MAPS_API_KEY
            }
            geocode_res = requests.get(geocode_url, params=params)
            geocode_data = geocode_res.json()
            
            if not geocode_data.get('results'):
                return Response(
                    {"error": "No se encontró la localidad. Intentá con otro nombre."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extraer coordenadas y nombre completo
            result = geocode_data['results'][0]
            location = result['geometry']['location']
            formatted_address = result['formatted_address']
            
            # Crear o actualizar localidad
            localidad, created = LocalidadUsuario.objects.update_or_create(
                user=request.user,
                defaults={
                    'nombre_localidad': formatted_address,
                    'latitud': location['lat'],
                    'longitud': location['lng'],
                    'activo': True
                }
            )
            
            serializer = LocalidadUsuarioSerializer(localidad)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Error al procesar la localidad: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request):
        try:
            localidad = request.user.localidad_outdoor
            localidad.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except LocalidadUsuario.DoesNotExist:
            return Response({"detail": "No tiene localidad configurada"}, status=status.HTTP_404_NOT_FOUND)


class LocalidadClimaView(APIView):
    """
    GET: Obtener último registro de clima para la localidad del usuario
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            localidad = request.user.localidad_outdoor
            # Obtener último registro de clima
            ultimo_registro = RegistroClima.objects.filter(
                localidad=localidad
            ).order_by('-fecha').first()
            
            if not ultimo_registro:
                return Response(
                    {"error": "No hay datos de clima disponibles"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({
                'temperatura_max': ultimo_registro.temperatura_max,
                'temperatura_min': ultimo_registro.temperatura_min,
                'humedad_promedio': ultimo_registro.humedad_promedio,
                'precipitacion_mm': ultimo_registro.precipitacion_mm,
                'velocidad_viento_kmh': ultimo_registro.velocidad_viento_kmh,
                'fecha': ultimo_registro.fecha
            })
            
        except LocalidadUsuario.DoesNotExist:
            return Response(
                {"error": "No tiene localidad configurada"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class TriggerRecalculoOutdoorView(APIView):
    """
    POST: Trigger manual para recalcular riegos outdoor ahora (útil para testing)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from plantas.services.weather_service import obtener_clima_para_usuario
        from plantas.services.outdoor_calculator import recalcular_fecha_riego_outdoor
        from plantas.models import Planta
        
        # Obtener y guardar clima actual
        registro = obtener_clima_para_usuario(request.user)
        
        if registro is None:
            return Response(
                {"error": "No se pudo obtener el clima. Verificá que tengas una localidad outdoor configurada."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Recalcular plantas outdoor
        plantas = Planta.objects.filter(usuario=request.user, tipo_cultivo='outdoor')
        resultados = []
        
        for planta in plantas:
            resultado = recalcular_fecha_riego_outdoor(planta, registro)
            resultados.append({
                'planta': planta.nombre_personalizado,
                'fecha_proximo_riego': resultado['fecha_proximo_riego'],
                'ajuste_aplicado': resultado['ajuste_aplicado'],
                'motivo': resultado['motivo']
            })
        
        return Response({
            'mensaje': f'Recálculo completado para {len(resultados)} plantas',
            'clima': {
                'temperatura_max': registro.temperatura_max,
                'humedad': registro.humedad_promedio,
                'precipitacion': registro.precipitacion_mm
            },
            'resultados': resultados
        })

class GoogleCalendarStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Verifica si el usuario actual ha vinculado su cuenta de Google Calendar.
        """
        user = request.user
        is_linked = False
        if hasattr(user, 'profile') and user.profile.google_access_token:
            is_linked = True
        return Response({'is_linked': is_linked})

class GoogleCalendarDisconnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Desvincula la cuenta de Google Calendar del usuario, eliminando sus credenciales.
        """
        user = request.user
        if not hasattr(user, 'profile'):
            return Response({"error": "Perfil no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        profile = user.profile

        # 1. Si el usuario tiene un token, intentar eliminar los eventos existentes ANTES de borrar el token.
        if profile.google_access_token:
            try:
                # Usamos la función helper para borrar eventos (maneja 404/410)
                from notificaciones.services.google_calendar import delete_calendar_event
                
                # Restauramos la query que se perdió en la edición anterior
                plantas_con_evento = Planta.objects.filter(usuario=user, google_calendar_event_id__isnull=False)
                
                for planta in plantas_con_evento:
                    # Intentamos borrar de Google Calendar
                    borrado_exitoso = delete_calendar_event(user, planta.google_calendar_event_id)
                    
                    if borrado_exitoso:
                        logger.info(f"Evento de Google Calendar eliminado: {planta.google_calendar_event_id} (planta: {planta.nombre_personalizado})")
                    else:
                        logger.warning(f"No se pudo confirmar borrado del evento {planta.google_calendar_event_id} (planta: {planta.nombre_personalizado})")

                    # CRÍTICO: Siempre limpiamos el ID en la base de datos para no quedar desincronizados.
                    # Si el evento sigue en Google (por error), es mejor perder el link que tener un ID fantasma.
                    planta.google_calendar_event_id = None
                    planta.save(update_fields=['google_calendar_event_id'])

            except Exception as e:
                # Si falla la obtención del servicio (ej. token expirado), solo lo informamos y continuamos.
                logger.warning(f"No se pudieron eliminar eventos del calendario al desvincular: {e}")

        # 2. Borrar los tokens y la información de Google del perfil.
        profile.google_access_token = None
        profile.google_refresh_token = None
        profile.google_token_expiry = None
        profile.save()
        
        # Registrar auditoría
        AuditLog.log(user, 'CALENDAR_UNLINK', request)
        logger.info(f"Google Calendar desvinculado para usuario: {user.username}")
        
        return Response({"message": "Calendario desvinculado con éxito. Los eventos asociados han sido eliminados."}, status=status.HTTP_200_OK)

class WeatherDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Obtiene datos del clima para una localidad usando la Weather API de Google.
        Espera un parámetro en la URL: /api/weather/?location=Cordoba,Argentina
        """
        location = request.query_params.get('location')
        if not location:
            return Response({"error": "La localidad es requerida."}, status=status.HTTP_400_BAD_REQUEST)

        api_key = settings.GOOGLE_MAPS_API_KEY
        # Primero, necesitamos geocodificar la localidad para obtener latitud y longitud
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
        
        try:
            geocode_response = requests.get(geocode_url)
            geocode_response.raise_for_status()  # Lanza un error si el status no es 2xx
            geocode_data = geocode_response.json()
            if not geocode_data.get('results'):
                return Response({"error": "No se pudo encontrar la localidad."}, status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Error al contactar Google Geocoding API: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError: # JSONDecodeError hereda de ValueError
            return Response({"error": "Respuesta inválida de Google Geocoding API. Verificá la API Key y que la API esté habilitada."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Extraemos latitud y longitud de la respuesta de Geocoding
        location_coords = geocode_data['results'][0]['geometry']['location']
        lat = location_coords.get('lat')
        lng = location_coords.get('lng')
        
        # Ahora pedimos el clima para esas coordenadas
        weather_url = f"https://weather.googleapis.com/v1/currentConditions:lookup?key={api_key}&location.latitude={lat}&location.longitude={lng}"
        try:
            # La llamada correcta es un GET con los parámetros en la URL
            weather_response = requests.get(weather_url)
            weather_response.raise_for_status()
            return Response(weather_response.json(), status=weather_response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Error al contactar Google Weather API: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError:
            return Response({"error": "Respuesta inválida de Google Weather API. Verificá la API Key y que la API esté habilitada."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -------- Plantas --------
class PlantaViewSet(viewsets.ModelViewSet):
    serializer_class = PlantaSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Cada usuario sólo ve sus plantas
        return Planta.objects.filter(usuario=self.request.user).order_by("id")

    def perform_create(self, serializer):
        planta = serializer.save()  # el serializer setea usuario desde request
        
        # Registrar auditoría
        AuditLog.log(
            self.request.user, 
            'PLANT_CREATE', 
            self.request, 
            details={
                'plant_name': planta.nombre_personalizado,
                'plant_type': planta.tipo_planta,
                'cultivation_type': planta.tipo_cultivo
            }
        )
        logger.info(f"Nueva planta creada: {planta.nombre_personalizado} por {self.request.user.username}")
    
    def perform_destroy(self, instance):
        plant_name = instance.nombre_personalizado
        user = self.request.user
        
        # Registrar auditoría ANTES de eliminar
        AuditLog.log(
            user, 
            'PLANT_DELETE', 
            self.request, 
            details={'plant_name': plant_name}
        )
        logger.info(f"Planta eliminada: {plant_name} por {user.username}")
        
        instance.delete()


    @action(detail=True, methods=['get'])
    def estado(self, request, pk=None):
        planta = self.get_object()
        
        # Intentar obtener configuración indoor del usuario
        temperatura = None
        humedad = None
        if hasattr(request.user, 'configuracion_cultivo'):
            config = request.user.configuracion_cultivo
            temperatura = config.temperatura_promedio
            humedad = config.humedad_relativa
        
        datos = planta.calculos_riego(temperatura_externa=temperatura, humedad_externa=humedad)
        
        # Agregar información sobre si se usó configuración indoor
        datos['usando_config_indoor'] = temperatura is not None or humedad is not None
        
        return Response(datos)
    
    @action(detail=True, methods=['post'], url_path='imagenes')
    def upload_image(self, request, pk=None):
        """
        Sube una imagen para una planta específica.
        POST /api/plantas/{id}/imagenes/
        Body: multipart/form-data con campo 'image'
        """
        planta = self.get_object()  # Verifica permisos automáticamente
        
        # Validar que se envió un archivo
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No se encontró el archivo. Use el campo "image".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        imagen_file = request.FILES['image']
        
        try:
            # Inicializar servicio de storage
            storage_service = PlantImageStorageService()
            
            # Subir imagen a GCS
            public_url, blob_name = storage_service.upload_image(imagen_file, planta.id)
            
            # Crear registro en base de datos
            imagen_planta = ImagenPlanta.objects.create(
                planta=planta,
                imagen_url=public_url,
                gcs_blob_name=blob_name
            )
            
            serializer = ImagenPlantaSerializer(imagen_planta)
            logger.info(f"Imagen subida exitosamente para planta {planta.nombre_personalizado}: {blob_name}")
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            # Errores de validación (tipo, tamaño, formato)
            logger.warning(f"Error de validación al subir imagen: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Errores inesperados
            logger.error(f"Error al subir imagen: {e}")
            return Response(
                {'error': 'Error al procesar la imagen. Intente nuevamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], url_path='imagenes/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """
        Elimina una imagen específica de una planta.
        DELETE /api/plantas/{id}/imagenes/{image_id}/
        """
        planta = self.get_object()  # Verifica permisos automáticamente
        
        try:
            # Buscar la imagen que pertenece a esta planta
            imagen = ImagenPlanta.objects.get(id=image_id, planta=planta)
        except ImagenPlanta.DoesNotExist:
            return Response(
                {'error': 'Imagen no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Eliminar de GCS
            storage_service = PlantImageStorageService()
            storage_service.delete_image(imagen.gcs_blob_name)
            
            # Eliminar registro de base de datos
            blob_name = imagen.gcs_blob_name
            imagen.delete()
            
            logger.info(f"Imagen eliminada exitosamente: {blob_name}")
            return Response(
                {'message': 'Imagen eliminada correctamente'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            logger.error(f"Error al eliminar imagen: {e}")
            return Response(
                {'error': 'Error al eliminar la imagen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def recalcular(self, request, pk=None):
        """
        Recalcula el estado de riego de una planta usando temperatura y humedad externas.
        Parámetros opcionales: /api/plantas/{id}/recalcular/?temperatura=25&humedad=60
        Si no se pasan parámetros, usa la configuración indoor del usuario.
        """
        planta = self.get_object()
       
        # Intentar obtener parámetros de la query string
        temperatura_str = request.query_params.get('temperatura')
        humedad_str = request.query_params.get('humedad')
        
        # Si no se pasaron parámetros, usar config indoor del usuario
        temperatura = None
        humedad = None
        
        if temperatura_str is not None:
            temperatura = float(temperatura_str)
        elif hasattr(request.user, 'configuracion_cultivo') and request.user.configuracion_cultivo.temperatura_promedio is not None:
            temperatura = request.user.configuracion_cultivo.temperatura_promedio
            
        if humedad_str is not None:
            humedad = float(humedad_str)
        elif hasattr(request.user, 'configuracion_cultivo') and request.user.configuracion_cultivo.humedad_relativa is not None:
            humedad = request.user.configuracion_cultivo.humedad_relativa
        
        datos_recalculados = planta.calculos_riego(temperatura_externa=temperatura, humedad_externa=humedad)
        datos_recalculados['usando_config_indoor'] = temperatura is not None or humedad is not None
        
        return Response(datos_recalculados)

    @action(detail=True, methods=['post'])
    def regar(self, request, pk=None):
        """
        Crea un registro de riego para esta planta y actualiza fecha_ultimo_riego.
        Body opcional: { "cantidad_agua_ml": 800, "comentarios": "Riego liviano" }
        """
        planta = self.get_object()
        data = {
            "planta": planta.id,
            "cantidad_agua_ml": request.data.get("cantidad_agua_ml"),
            "comentarios": request.data.get("comentarios", ""),
        }
        serializer = RiegoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        riego = serializer.save()
        return Response(RiegoSerializer(riego).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """
        Devuelve el historial de riegos y estadísticas para una planta específica.
        Optimizado para reducir consultas a la base de datos.
        """
        planta = self.get_object()
        
        # Traemos todos los riegos ordenados en una sola query
        # Usamos list() para evaluar el queryset una sola vez y trabajar en memoria
        # ya que necesitamos iterar varias veces sobre los mismos datos (análisis, gráfico, tabla)
        todos_riegos = list(planta.riegos.all().order_by('-fecha'))
        
        if not todos_riegos:
            # Respuesta rápida si no hay datos
            return Response({
                'estadisticas': {
                    'total_riegos': 0, 'total_agua_ml': 0, 'promedio_agua_ml': 0,
                    'max_agua_ml': 0, 'min_agua_ml': 0, 'primer_riego_fecha': None,
                    'ultimo_riego_fecha': None, 'frecuencia_promedio_dias': None
                },
                'historial_riegos': [],
                'tendencias': {},
                'anomalias': []
            })

        # --- 1. Cálculo de Estadísticas (en Python para evitar otra query) ---
        total_riegos = len(todos_riegos)
        cantidades = [r.cantidad_agua_ml for r in todos_riegos if r.cantidad_agua_ml is not None]
        fechas = [r.fecha for r in todos_riegos]
        
        total_agua = sum(cantidades)
        promedio_agua = total_agua / len(cantidades) if cantidades else 0
        max_agua = max(cantidades) if cantidades else 0
        min_agua = min(cantidades) if cantidades else 0
        
        # --- Cálculo de Frecuencia Promedio ---
        frecuencia_promedio_dias = None
        if total_riegos > 1:
            diferencias = [(fechas[i] - fechas[i+1]).days for i in range(len(fechas)-1)]
            if diferencias:
                frecuencia_promedio_dias = sum(diferencias) / len(diferencias)

        estadisticas = {
            'total_riegos': total_riegos,
            'total_agua_ml': total_agua,
            'promedio_agua_ml': round(promedio_agua, 1),
            'max_agua_ml': max_agua,
            'min_agua_ml': min_agua,
            'primer_riego_fecha': fechas[-1],   # El último de la lista (porque está ordenado DESC) es el primero cronológicamente
            'ultimo_riego_fecha': fechas[0],    # El primero de la lista es el último cronológicamente
            'frecuencia_promedio_dias': round(frecuencia_promedio_dias, 1) if frecuencia_promedio_dias is not None else None,
        }

        # --- 2. Análisis de Tendencias ---
        tendencias = {}
        if total_riegos >= 5 and frecuencia_promedio_dias:
            # Últimos 5 riegos (ya los tenemos en memoria)
            # fechas[0] es el más reciente, fechas[4] es el 5to más reciente
            ultimos_5_fechas = fechas[:5]
            diferencias_ultimos = [(ultimos_5_fechas[i] - ultimos_5_fechas[i+1]).days for i in range(len(ultimos_5_fechas)-1)]
            
            if diferencias_ultimos:
                frecuencia_reciente = sum(diferencias_ultimos) / len(diferencias_ultimos)
                variacion = frecuencia_reciente - frecuencia_promedio_dias
                
                if variacion > 1:
                    tendencias['mensaje'] = f"La frecuencia de riego está disminuyendo (cada {round(frecuencia_reciente, 1)} días vs promedio de {round(frecuencia_promedio_dias, 1)} días)"
                    tendencias['tipo'] = 'disminuyendo'
                elif variacion < -1:
                    tendencias['mensaje'] = f"La frecuencia de riego está aumentando (cada {round(frecuencia_reciente, 1)} días vs promedio de {round(frecuencia_promedio_dias, 1)} días)"
                    tendencias['tipo'] = 'aumentando'
                else:
                    tendencias['mensaje'] = "La frecuencia de riego se mantiene estable"
                    tendencias['tipo'] = 'estable'
                    
                tendencias['frecuencia_reciente'] = round(frecuencia_reciente, 1)
                tendencias['variacion_dias'] = round(variacion, 1)

        # --- 3. Detección de Anomalías ---
        anomalias = []
        
        # Riegos frecuentes
        if total_riegos >= 3:
            # Analizamos los últimos 3 riegos
            dias_entre_ultimos_3 = (fechas[0] - fechas[2]).days
            if dias_entre_ultimos_3 <= 3:
                anomalias.append({
                    'tipo': 'riegos_frecuentes',
                    'mensaje': f"⚠️ Se detectaron 3 riegos en {dias_entre_ultimos_3} días. Verificá si la planta necesita tanta agua.",
                    'severidad': 'media'
                })
        
        # Cantidades anormales (analizamos solo los últimos 5 para no saturar)
        for riego in todos_riegos[:5]:
            if riego.cantidad_agua_ml:
                if promedio_agua > 0 and riego.cantidad_agua_ml > promedio_agua * 2:
                    anomalias.append({
                        'tipo': 'agua_excesiva',
                        'mensaje': f"⚠️ Riego del {riego.fecha}: {riego.cantidad_agua_ml}ml es más del doble del promedio ({round(promedio_agua)}ml)",
                        'severidad': 'alta',
                        'fecha': riego.fecha
                    })
                elif promedio_agua > 0 and riego.cantidad_agua_ml < promedio_agua * 0.3:
                    anomalias.append({
                        'tipo': 'agua_insuficiente',
                        'mensaje': f"ℹ️ Riego del {riego.fecha}: {riego.cantidad_agua_ml}ml es menos del 30% del promedio ({round(promedio_agua)}ml)",
                        'severidad': 'baja',
                        'fecha': riego.fecha
                    })

        # Serializamos usando el serializer pero con many=True sobre la lista que ya tenemos
        serializer = RiegoSerializer(todos_riegos, many=True)
        
        return Response({
            'estadisticas': estadisticas, 
            'historial_riegos': serializer.data,
            'tendencias': tendencias,
            'anomalias': anomalias
        })

# -------- Riegos --------
class RiegoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Sólo lectura global, pero filtrable por ?planta=<id>.
    Para crear riegos usá la acción POST /plantas/{id}/regar/
    """
    serializer_class = RiegoSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = Riego.objects.select_related("planta").filter(
            planta__usuario=self.request.user
        ).order_by("-fecha", "-id")

        planta_id = self.request.query_params.get("planta")
        if planta_id:
            queryset = queryset.filter(planta_id=planta_id)
        
        return queryset


# ========== ELIMINAR CUENTA ==========
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from notificaciones.services.google_calendar import delete_calendar_event
from notificaciones.models import Profile as NotificationProfile
import traceback

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def delete_account(request):
    """
    Elimina permanentemente la cuenta del usuario y todos sus datos.
    
    Orden de eliminación:
    1. Desvincular Google Calendar (si está vinculado) - borrar eventos
    2. Eliminar plantas (cascade: registros de riego)
    3. Eliminar configuraciones
    4. Eliminar perfil de notificaciones
    5. Eliminar usuario
    """
    user = request.user
    username = user.username  # Guardar antes de eliminar
    user_email = user.email
    
    try:
        logger.info(f"Iniciando eliminación de cuenta: {username}")
        
        # 1. Verificar si tiene Google Calendar vinculado y borrar eventos
        eventos_eliminados = 0
        try:
            profile = NotificationProfile.objects.get(user=user)
            logger.debug(f"Perfil de notificaciones encontrado para {username}")
            if profile.google_access_token:
                logger.info(f"Eliminando eventos de Google Calendar para {username}")
                # Borrar todos los eventos de Google Calendar antes de eliminar
                plantas_con_evento = Planta.objects.filter(
                    usuario=user, 
                    google_calendar_event_id__isnull=False
                )
                
                for planta in plantas_con_evento:
                    try:
                        delete_calendar_event(user, planta.google_calendar_event_id)
                        eventos_eliminados += 1
                        logger.debug(f"Evento {planta.google_calendar_event_id} eliminado")
                    except Exception as e:
                        # Si falla el borrado de un evento, continuamos
                        logger.warning(f"Error al borrar evento {planta.google_calendar_event_id}: {e}")
        except NotificationProfile.DoesNotExist:
            logger.debug(f"Usuario {username} no tiene perfil de notificaciones")
            pass
        
        logger.info(f"Eliminando plantas del usuario {username}...")
        # 2. Eliminar plantas (los registros se eliminan en cascada por ForeignKey)
        plantas_count = Planta.objects.filter(usuario=user).count()
        Planta.objects.filter(usuario=user).delete()
        
        logger.info(f"Eliminando configuración del usuario {username}...")
        # 3. Eliminar configuración de usuario
        ConfiguracionUsuario.objects.filter(user=user).delete()
        
        logger.info(f"Eliminando localidad outdoor del usuario {username}...")
        # 4. Eliminar localidad outdoor
        LocalidadUsuario.objects.filter(user=user).delete()
        
        logger.info(f"Eliminando perfil de notificaciones del usuario {username}...")
        # 5. Eliminar perfil de notificaciones
        NotificationProfile.objects.filter(user=user).delete()
        
        # Registrar auditoría ANTES de eliminar el usuario
        AuditLog.log(
            user, 
            'DELETE_ACCOUNT', 
            request, 
            details={
                'plantas_eliminadas': plantas_count,
                'eventos_calendar_eliminados': eventos_eliminados,
                'email': user_email
            }
        )
        
        logger.warning(f"Eliminando usuario: {username}")
        # 6. Finalmente, eliminar el usuario
        user.delete()
        
        logger.info(f"Usuario {username} eliminado exitosamente (plantas: {plantas_count}, eventos: {eventos_eliminados})")
        return Response({
            'message': f'Cuenta de {username} eliminada exitosamente'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Si algo falla, la transacción se revierte automáticamente
        error_detail = traceback.format_exc()
        logger.error(f"Error al eliminar cuenta de {username}: {error_detail}")
        return Response({
            'detail': f'Error al eliminar cuenta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

