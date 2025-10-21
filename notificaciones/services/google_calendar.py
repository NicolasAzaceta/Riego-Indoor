import os
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import pytz
from django.conf import settings
from google.oauth2 import service_account, credentials
from googleapiclient.discovery import build

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.conf import settings
from django.utils import timezone
import json

CLIENT_SECRET_FILE = 'notificaciones/services/client_secret.json'

# Configurar el flujo de OAuth 2.0
def get_oauth_flow():
    return Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri='http://localhost:8000/google-calendar/oauth2callback/'  # Apunta a la vista de callback del backend
    )

# Obtener el servicio de Google Calendar con las credenciales OAuth del usuario
def get_user_calendar_service(user):
    with open(CLIENT_SECRET_FILE, 'r') as f:
        client_config = json.load(f)['web']

    profile = user.profile
    creds = Credentials(
        token=profile.google_access_token,
        refresh_token=profile.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_config.get('client_id'),
        client_secret=client_config.get('client_secret')
    )

    # --- LÓGICA CLAVE: Refrescar el token si es necesario ---
    # Verificamos si el token ha expirado o está a punto de expirar (ej. en los próximos 5 minutos)
    if creds.expired and creds.refresh_token:
        print(f"Token de Google para '{user.username}' expirado. Refrescando...")
        creds.refresh(credentials.Request())
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