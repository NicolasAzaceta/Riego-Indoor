from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


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