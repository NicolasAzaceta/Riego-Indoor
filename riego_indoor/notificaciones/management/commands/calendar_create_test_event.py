from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from notificaciones.services.google_calendar import create_calendar_event, DEFAULT_TZ, ensure_timezone




class Command(BaseCommand):
  help = (
   "Crea un evento de prueba en Google Calendar. "
    "Ejemplo: python manage.py calendar_create_test_event --calendar tu_mail@gmail.com"
    )


  def add_arguments(self, parser):
      parser.add_argument(
          '--calendar', required=True,
          help='ID del calendario (p. ej. tu_mail@gmail.com o el ID del calendario compartido)'
        )
      parser.add_argument(
          '--minutes', type=int, default=10,
          help='Cuántos minutos desde ahora para iniciar el evento (default: 10)'
        )
      parser.add_argument(
        '--duration', type=int, default=30,
        help='Duración en minutos del evento (default: 30)'
        )
      parser.add_argument(
        '--summary', default='Riego Planta Indoor 🌱 (TEST)',
        help='Título del evento'
    )


  def handle(self, *args, **options):
    calendar_id = options['calendar']
    minutes = options['minutes']
    duration = options['duration']
    summary = options['summary']


    now = ensure_timezone(datetime.now(), DEFAULT_TZ)
    start_dt = now + timedelta(minutes=minutes)
    end_dt = start_dt + timedelta(minutes=duration)


    try:
       event = create_calendar_event(
         calendar_id=calendar_id,
         summary=summary,
         start_dt=start_dt,
         end_dt=end_dt,
         description='Evento de prueba generado desde Django',
       )
    except Exception as e:
       raise CommandError(str(e))


    self.stdout.write(self.style.SUCCESS('Evento creado OK'))
    self.stdout.write(f"Link: {event.get('htmlLink')}")