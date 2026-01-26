"""
Servicio para interactuar con Google Weather API y gestionar registros climáticos.
"""

import requests
from django.conf import settings
from datetime import datetime, date
from plantas.models import RegistroClima, LocalidadUsuario


def obtener_clima_actual(latitud, longitud):
    """
    Obtiene datos del clima actual de Google Weather API.
    
    Args:
        latitud: float
        longitud: float
    
    Returns:
        dict con datos meteorológicos o None si hay error
        {
            'temperatura_max': float,
            'temperatura_min': float,
            'humedad_promedio': float,
            'precipitacion_mm': float,
            'velocidad_viento_kmh': float
        }
    
    Raises:
        requests.exceptions.RequestException: Si hay error en la API
    """
    api_key = settings.GOOGLE_MAPS_API_KEY
    url = f"https://weather.googleapis.com/v1/currentConditions:lookup?key={api_key}&location.latitude={latitud}&location.longitude={longitud}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Parsear respuesta de Google Weather API
        # Estructura: https://developers.google.com/maps/documentation/weather/reference/rest
        
        # Temperatura (viene en Celsius por defecto)
        temp_celsius = data.get('temperature', {}).get('value', 20.0)
        
        # Humedad (porcentaje)
        humedad = data.get('relativeHumidity', {}).get('value', 50.0)
        
        # Precipitación (mm)
        precipitacion = data.get('precipitation', {}).get('value', 0.0)
        
        # Viento (m/s -> km/h)
        viento_ms = data.get('wind', {}).get('speed', {}).get('value', 0.0)
        viento_kmh = viento_ms * 3.6
        
        return {
            'temperatura_max': temp_celsius,  # Asumimos temp actual como max
            'temperatura_min': temp_celsius - 5,  # Estimación conservadora
            'humedad_promedio': humedad,
            'precipitacion_mm': precipitacion,
            'velocidad_viento_kmh': viento_kmh
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar Weather API: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error al parsear respuesta de Weather API: {e}")
        return None


def guardar_registro_clima(localidad, datos_clima, fecha=None):
    """
    Guarda un registro del clima en la base de datos.
    
    Args:
        localidad: Instancia de LocalidadUsuario
        datos_clima: Dict con datos meteorológicos
        fecha: date object (opcional, default: hoy)
    
    Returns:
        RegistroClima instance creado o actualizado
    """
    if fecha is None:
        fecha = date.today()
    
    registro, created = RegistroClima.objects.update_or_create(
        localidad=localidad,
        fecha=fecha,
        defaults={
            'temperatura_max': datos_clima.get('temperatura_max', 20.0),
            'temperatura_min': datos_clima.get('temperatura_min', 15.0),
            'humedad_promedio': datos_clima.get('humedad_promedio', 50.0),
            'precipitacion_mm': datos_clima.get('precipitacion_mm', 0.0),
            'velocidad_viento_kmh': datos_clima.get('velocidad_viento_kmh', 0.0),
        }
    )
    
    # Actualizar timestamp de última actualización
    localidad.ultima_actualizacion_clima = datetime.now()
    localidad.save(update_fields=['ultima_actualizacion_clima'])
    
    return registro


def obtener_y_guardar_clima(localidad):
    """
    Obtiene clima actual y lo guarda en la base de datos.
    
    Args:
        localidad: Instancia de LocalidadUsuario
    
    Returns:
        RegistroClima instance o None si hay error
    """
    datos = obtener_clima_actual(localidad.latitud, localidad.longitud)
    
    if datos is None:
        return None
    
    return guardar_registro_clima(localidad, datos)


def obtener_clima_para_usuario(user):
    """
    Obtiene y guarda el clima para la localidad outdoor de un usuario.
    
    Args:
        user: User instance
    
    Returns:
        RegistroClima instance o None si el usuario no tiene localidad outdoor
    """
    try:
        localidad = user.localidad_outdoor
        if not localidad.activo:
            return None
        
        return obtener_y_guardar_clima(localidad)
    
    except LocalidadUsuario.DoesNotExist:
        return None
