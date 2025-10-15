from django.urls import path
from notificaciones.api.views import CalendarEventCreateView
from .views import CustomTokenObtainPairView, google_calendar_auth, google_calendar_callback


urlpatterns = [
     path('calendar/events/', CalendarEventCreateView.as_view(), name='calendar-event-create'),
     path('auth/', google_calendar_auth, name='google_calendar_auth'),
     path('oauth2callback/', google_calendar_callback, name='oauth2callback'),
     path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]
