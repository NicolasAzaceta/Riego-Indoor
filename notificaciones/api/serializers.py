from rest_framework import serializers
from datetime import datetime, timedelta
from notificaciones.services.google_calendar import parse_datetime


class EventCreateSerializer(serializers.Serializer):
     calendar_id = serializers.EmailField(help_text='Ej: tu_mail@gmail.com')
     summary = serializers.CharField(max_length=200)
     description = serializers.CharField(required=False, allow_blank=True)
     start_time = serializers.CharField(
          help_text='Fecha/hora ISO. Ej: 2025-09-02T21:00:00 o 2025-09-02T21:00:00-03:00'
     )
     duration_minutes = serializers.IntegerField(min_value=1, default=30)


     def validate(self, attrs):
        start_dt = parse_datetime(attrs['start_time'])
        attrs['start_dt'] = start_dt
        attrs['end_dt'] = start_dt + timedelta(minutes=attrs['duration_minutes'])
        return attrs