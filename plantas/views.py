from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from .models import Planta, Riego, ConfiguracionUsuario, LocalidadUsuario, RegistroClima
from .serializers import PlantaSerializer, RiegoSerializer, RegisterSerializer, ConfiguracionUsuarioSerializer, LocalidadUsuarioSerializer
from .permissions import IsOwner
from notificaciones.services.google_calendar import get_user_calendar_service

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, Max, Min, Value
from django.db.models.functions import Coalesce
from django.contrib.auth import login, authenticate
from django.conf import settings
import requests


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
                service = get_user_calendar_service(user)
                plantas_con_evento = Planta.objects.filter(usuario=user, google_calendar_event_id__isnull=False)
                
                for planta in plantas_con_evento:
                    try:
                        service.events().delete(calendarId='primary', eventId=planta.google_calendar_event_id).execute()
                        print(f"Evento '{planta.google_calendar_event_id}' de la planta '{planta.nombre_personalizado}' eliminado por desvinculación.")
                    except Exception as e:
                        print(f"No se pudo eliminar el evento '{planta.google_calendar_event_id}' (puede que ya no exista): {e}")
            except Exception as e:
                # Si falla la obtención del servicio (ej. token expirado), solo lo informamos y continuamos.
                print(f"No se pudieron eliminar los eventos del calendario al desvincular (posiblemente el token ya no era válido): {e}")

        # 2. Borrar los tokens y la información de Google del perfil.
        profile.google_access_token = None
        profile.google_refresh_token = None
        profile.google_token_expiry = None
        profile.save()
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
        serializer.save()  # el serializer setea usuario desde request

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
        Responde con un JSON que contiene:
        - `estadisticas`: Datos agregados como promedios, totales, etc.
        - `historial_riegos`: Una lista de todos los registros de riego.
        - `tendencias`: Análisis de tendencias en el patrón de riego.
        - `anomalias`: Detección de patrones inusuales.
        """
        planta = self.get_object()
        historial_riegos_qs = planta.riegos.all().order_by('-fecha')

        # --- 1. Cálculo de Estadísticas ---
        # Usamos el ORM de Django para que la base de datos haga el trabajo pesado.
        estadisticas_db = historial_riegos_qs.aggregate(
            total_riegos=Count('id'),
            total_agua_ml=Sum(Coalesce('cantidad_agua_ml', Value(0))),
            promedio_agua_ml=Avg(Coalesce('cantidad_agua_ml', Value(0))),
            max_agua_ml=Max('cantidad_agua_ml'),
            min_agua_ml=Min('cantidad_agua_ml'),
            primer_riego_fecha=Min('fecha'),
            ultimo_riego_fecha=Max('fecha')
        )

        # --- Cálculo de Frecuencia Promedio (requiere un poco de Python) ---
        frecuencia_promedio_dias = None
        if historial_riegos_qs.count() > 1:
            # Obtenemos solo las fechas, ya ordenadas por el queryset
            fechas_riegos = list(historial_riegos_qs.values_list('fecha', flat=True))
            # Calculamos la diferencia en días entre riegos consecutivos
            diferencias = [(fechas_riegos[i-1] - fechas_riegos[i]).days for i in range(1, len(fechas_riegos))]
            if diferencias:
                frecuencia_promedio_dias = sum(diferencias) / len(diferencias)

        # --- 2. Análisis de Tendencias ---
        tendencias = {}
        if historial_riegos_qs.count() >= 5:
            # Comparar últimos 5 riegos vs promedio general
            ultimos_5 = list(historial_riegos_qs.values_list('fecha', flat=True)[:5])
            diferencias_ultimos = [(ultimos_5[i-1] - ultimos_5[i]).days for i in range(1, len(ultimos_5))]
            
            if diferencias_ultimos and frecuencia_promedio_dias:
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
        
        # Detectar riegos muy frecuentes (3 o más riegos en 3 días)
        if historial_riegos_qs.count() >= 3:
            ultimos_3 = list(historial_riegos_qs.values_list('fecha', flat=True)[:3])
            dias_entre_ultimos_3 = (ultimos_3[0] - ultimos_3[2]).days
            
            if dias_entre_ultimos_3 <= 3:
                anomalias.append({
                    'tipo': 'riegos_frecuentes',
                    'mensaje': f"⚠️ Se detectaron {len(ultimos_3)} riegos en {dias_entre_ultimos_3} días. Verificá si la planta necesita tanta agua.",
                    'severidad': 'media'
                })
        
        # Detectar cantidades anormales de agua
        if estadisticas_db['promedio_agua_ml'] and estadisticas_db['promedio_agua_ml'] > 0:
            riegos_recientes = historial_riegos_qs[:5]
            for riego in riegos_recientes:
                if riego.cantidad_agua_ml:
                    if riego.cantidad_agua_ml > estadisticas_db['promedio_agua_ml'] * 2:
                        anomalias.append({
                            'tipo': 'agua_excesiva',
                            'mensaje': f"⚠️ Riego del {riego.fecha}: {riego.cantidad_agua_ml}ml es más del doble del promedio ({round(estadisticas_db['promedio_agua_ml'])}ml)",
                            'severidad': 'alta',
                            'fecha': riego.fecha
                        })
                    elif riego.cantidad_agua_ml < estadisticas_db['promedio_agua_ml'] * 0.3:
                        anomalias.append({
                            'tipo': 'agua_insuficiente',
                            'mensaje': f"ℹ️ Riego del {riego.fecha}: {riego.cantidad_agua_ml}ml es menos del 30% del promedio ({round(estadisticas_db['promedio_agua_ml'])}ml)",
                            'severidad': 'baja',
                            'fecha': riego.fecha
                        })

        # --- 4. Construcción del objeto de respuesta ---
        estadisticas = {
            'total_riegos': estadisticas_db['total_riegos'] or 0,
            'total_agua_ml': estadisticas_db['total_agua_ml'] or 0,
            'promedio_agua_ml': round(estadisticas_db['promedio_agua_ml'], 1) if estadisticas_db['promedio_agua_ml'] else 0,
            'max_agua_ml': estadisticas_db['max_agua_ml'] or 0,
            'min_agua_ml': estadisticas_db['min_agua_ml'] or 0,
            'primer_riego_fecha': estadisticas_db['primer_riego_fecha'],
            'ultimo_riego_fecha': estadisticas_db['ultimo_riego_fecha'],
            'frecuencia_promedio_dias': round(frecuencia_promedio_dias, 1) if frecuencia_promedio_dias is not None else None,
        }

        # Serializamos el historial para la segunda parte de la respuesta
        serializer = RiegoSerializer(historial_riegos_qs, many=True)
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
        qs = Riego.objects.select_related("planta", "planta__usuario").all().order_by("-fecha", "-id")
        qs = [r for r in qs if r.planta.usuario == self.request.user]
        planta_id = self.request.query_params.get("planta")
        if planta_id:
            qs = [r for r in qs if str(r.planta_id) == str(planta_id)]
        # Convertimos a queryset-like (lista está bien para ReadOnly con DRF, pero si querés queryset real, usá filtrado por ORM)
        from django.db.models.query import QuerySet
        return qs  # DRF acepta iterables; si preferís, cambiamos el enfoque a ORM puro.


