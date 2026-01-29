from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import threading


from notificaciones.api.serializers import EventCreateSerializer
from notificaciones.services.google_calendar import create_calendar_event




class CalendarEventCreateView(APIView):
   def post(self, request):
       serializer = EventCreateSerializer(data=request.data)
       serializer.is_valid(raise_exception=True)
       data = serializer.validated_data


       event = create_calendar_event(
           calendar_id=data['calendar_id'],
           summary=data['summary'],
           start_dt=data['start_dt'],
           end_dt=data['end_dt'],
           description=data.get('description', ''),
        )


       return Response({
           'message': 'Evento creado',
           'event_id': event.get('id'),
           'htmlLink': event.get('htmlLink'),
        }, status=status.HTTP_201_CREATED)


class UpdateCalendarTimeView(APIView):
    """
    Endpoint para leer y actualizar la hora preferida de los eventos del calendario.
    """
    
    def get(self, request):
        if not hasattr(request.user, 'profile'):
            return Response({"error": "Perfil no encontrado"}, status=status.HTTP_404_NOT_FOUND)
            
        profile = request.user.profile
        is_linked = bool(profile.google_access_token)
        
        return Response({
            "google_calendar_event_time": profile.google_calendar_event_time,
            "is_linked": is_linked
        })

    def patch(self, request):
        if not hasattr(request.user, 'profile'):
             return Response({"error": "Perfil no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        profile = request.user.profile
        
        # Validar vinculación
        if not profile.google_access_token:
            return Response(
                {"error": "Debés vincular tu cuenta de Google Calendar primero."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        time_value = request.data.get("time")
        if not time_value:
             return Response({"error": "Falta el campo 'time'"}, status=status.HTTP_400_BAD_REQUEST)
             
        try:
            # Validar formato de hora (HH:MM o HH:MM:SS)
            # Django TimeField maneja strings, pero validamos básico
            
            # --- NUEVO: Asegurar que la hora se guarde como naive si viene como string ---
            # Si el frontend manda un string como "10:00", Django lo puede parsear bien.
            # El problema es evitar cualquier transformación extraña de zona horaria antes de guardar.
            
            # (Opcional) Parsear manualmente para estar 100% seguros
            from django.utils.dateparse import parse_time
            parsed_time = parse_time(str(time_value))
            if parsed_time is None:
                 return Response({"error": "Formato de hora inválido. Usar HH:MM"}, status=status.HTTP_400_BAD_REQUEST)
            
            profile.google_calendar_event_time = parsed_time
            profile.save()
            
            # Recalcular eventos futuros en un hilo separado para no bloquear la respuesta
            from notificaciones.services.google_calendar import recalculate_all_future_events
            
            def run_recalculation(user):
                try:
                    recalculate_all_future_events(user)
                    print(f"Recálculo en segundo plano finalizado para {user.username}")
                except Exception as e:
                    print(f"Error en recálculo en segundo plano: {e}")

            thread = threading.Thread(target=run_recalculation, args=(request.user,))
            thread.daemon = True # El hilo muere si el proceso principal muere
            thread.start()
            
            msg = "Hora actualizada. Los eventos se están reprogramando en segundo plano."

            return Response({
                "message": msg,
                "google_calendar_event_time": profile.google_calendar_event_time
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)