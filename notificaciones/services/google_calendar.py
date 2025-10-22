# --- Librerías Estándar ---
import os
import json
from datetime import datetime, timedelta

# --- Librerías de Terceros ---
from dateutil import parser as dateparser
import pytz
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests # Para el refresh del token

# --- Componentes de Django ---
from django.conf import settings
from django.utils import timezone

def _get_redirect_uri():
    """Devuelve la URI de redirección correcta para desarrollo o producción."""
    if settings.DEBUG:
        return 'http://localhost:8000/google-calendar/oauth2callback/'
    
    # En producción, usamos el dominio de Render.
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if not hostname:
        # Fallback por si la variable no está disponible, aunque no debería pasar.
        return 'https://riegum.com/google-calendar/oauth2callback/'
    return f'https://{hostname}/google-calendar/oauth2callback/'

# Configurar el flujo de OAuth 2.0
def get_oauth_flow():
    """Crea el flujo OAuth desde variables de entorno (producción) o archivo (desarrollo)."""
    client_secrets_json_str = os.environ.get('GOOGLE_CLIENT_SECRET_JSON')
    scopes = ['https://www.googleapis.com/auth/calendar']
    redirect_uri = _get_redirect_uri()

    if client_secrets_json_str:
        # Producción: Cargar desde la variable de entorno
        client_config = json.loads(client_secrets_json_str)
        return Flow.from_client_config(client_config, scopes=scopes, redirect_uri=redirect_uri)
    
    # Desarrollo: Cargar desde el archivo local
    return Flow.from_client_secrets_file('notificaciones/services/client_secret.json', scopes=scopes, redirect_uri=redirect_uri)

# Obtener el servicio de Google Calendar con las credenciales OAuth del usuario
def get_user_calendar_service(user):
    profile = user.profile
    creds = Credentials(
        token=profile.google_access_token,
        refresh_token=profile.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET
    )

    # --- LÓGICA CLAVE: Refrescar el token si es necesario ---
    # Verificamos si el token ha expirado o está a punto de expirar (ej. en los próximos 5 minutos)
    if creds.expired and creds.refresh_token:
        print(f"Token de Google para '{user.username}' expirado. Refrescando...")
        creds.refresh(google_requests.Request())
        # Guardamos los nuevos tokens en el perfil del usuario
        profile.google_access_token = creds.token
        # Google a veces devuelve un nuevo refresh_token, aunque no siempre.
        if creds.refresh_token:
            profile.google_refresh_token = creds.refresh_token
        profile.google_token_expiry = creds.expiry
        profile.save()

    return build('calendar', 'v3', credentials=creds)


SCOPES = ['https://www.googleapis.com/auth/calendar']
DEFAULT_TZ = 'America/Argentina/Cordoba'




def _get_credentials_from_file():
    """Carga credenciales desde el archivo JSON en settings.GOOGLE_SERVICE_ACCOUNT_FILE."""
    cred_path = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', None)
    if not cred_path or not os.path.exists(cred_path):
       raise FileNotFoundError(
           f"No se encontró el archivo de credenciales en: {cred_path}. "
           "Verificá settings.GOOGLE_SERVICE_ACCOUNT_FILE y que el JSON exista."
        )   
    return service_account.Credentials.from_service_account_file(cred_path, scopes=SCOPES)




def get_service_account_calendar_service():
    """Construye y devuelve el cliente de Google Calendar API."""
    credentials = _get_credentials_from_file()
    service = build('calendar', 'v3', credentials=credentials)
    return service




def ensure_timezone(dt, tz_name: str = DEFAULT_TZ) -> datetime:
    """Asegura que un datetime sea timezone-aware en la tz indicada."""
    tz = pytz.timezone(tz_name)
    if dt.tzinfo is None:
      return tz.localize(dt)
    return dt.astimezone(tz)




def parse_datetime(value: str, tz_name: str = DEFAULT_TZ) -> datetime:
    """
    Acepta: "2025-09-02T21:00:00" (naive) o con offset "2025-09-02T21:00:00-03:00".
    Devuelve un datetime aware en la tz indicada.
    """
    dt = dateparser.parse(value)
    return ensure_timezone(dt, tz_name)




def create_calendar_event(
    calendar_id: str,
    summary: str,
    start_dt: datetime,
    end_dt: datetime,
    description: str | None = None,
    tz_name: str = DEFAULT_TZ,
    reminders_minutes: int = 10,
  ):
 """Crea un evento en Google Calendar y devuelve el dict del evento (incluye htmlLink)."""
 service = get_service_account_calendar_service() # Usamos la cuenta de servicio por defecto


 start_dt = ensure_timezone(start_dt, tz_name)
 end_dt = ensure_timezone(end_dt, tz_name)


 body = {
    'summary': summary,
    'description': description or '',
    'start': {
        'dateTime': start_dt.isoformat(),
        'timeZone': tz_name,
    },
    'end': {
        'dateTime': end_dt.isoformat(),
        'timeZone': tz_name,
   },
   'reminders': {
       'useDefault': False,
        'overrides': [
             {'method': 'popup', 'minutes': reminders_minutes},
     ],
    },
  }


 event = service.events().insert(calendarId=calendar_id, body=body).execute()
 return event