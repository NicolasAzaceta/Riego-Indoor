from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from .models import Planta, Riego
from .serializers import PlantaSerializer, RiegoSerializer, RegisterSerializer
from .permissions import IsOwner
from notificaciones.services.google_calendar import get_user_calendar_service

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, Max, Min
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
        datos = planta.calculos_riego()
        return Response(datos)

    @action(detail=True, methods=['get'])
    def recalcular(self, request, pk=None):
        """
        Recalcula el estado de riego de una planta usando una temperatura externa.
        Espera un parámetro: /api/plantas/{id}/recalcular/?temperatura=25
        """
        planta = self.get_object()
        temperatura_str = request.query_params.get('temperatura')
        if temperatura_str is None:
            return Response({"error": "El parámetro 'temperatura' es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        
        datos_recalculados = planta.calculos_riego(temperatura_externa=float(temperatura_str))
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
        """
        planta = self.get_object()
        historial_riegos_qs = planta.riegos.all().order_by('-fecha')

        # --- 1. Cálculo de Estadísticas ---
        # Usamos el ORM de Django para que la base de datos haga el trabajo pesado.
        estadisticas_db = historial_riegos_qs.aggregate(
            total_riegos=Count('id'),
            total_agua_ml=Sum('cantidad_agua_ml'),
            promedio_agua_ml=Avg('cantidad_agua_ml'),
            max_agua_ml=Max('cantidad_agua_ml'),
            min_agua_ml=Max('cantidad_agua_ml'),
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

        # --- 2. Construcción del objeto de respuesta ---
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
        return Response({'estadisticas': estadisticas, 'historial_riegos': serializer.data})

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


# -------- Usuarios --------
# class UserViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = User.objects.all().order_by("id")
#     serializer_class = RegisterSerializer
#     permission_classes = [IsAuthenticated]  # Sólo usuarios autenticados pueden ver la lista de usuarios

#     @action(detail=False, methods=['get'])
#     def me(self, request):
#         serializer = self.get_serializer(request.user)
#         return Response(serializer.data)
    
# Nota: para login/logout usá las vistas de rest_framework.urls o JWT.

# o HttpResponse("Bienvenido a la API de Riego Indoor")
# Alternativamente, podés usar HttpResponse si no querés template.
# Y en urls.py, mapeá la vista home_view a la ruta raíz o /home/ según prefieras.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):   
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
