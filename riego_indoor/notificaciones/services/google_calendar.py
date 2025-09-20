import os
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import pytz


from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build


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




def get_calendar_service():
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
 service = get_calendar_service()


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