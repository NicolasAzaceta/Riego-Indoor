from django.urls import path
from notificaciones.api.views import CalendarEventCreateView


urlpatterns = [
     path('calendar/events/', CalendarEventCreateView.as_view(), name='calendar-event-create'),
]