from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from notificaciones.views import CustomTokenObtainPairView
from plantas.views import GoogleCalendarStatusView, GoogleCalendarDisconnectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Vistas de Páginas (Frontend) ---
    # La raíz del sitio ('') y otras rutas como /login, /register, /dashboard, etc.
    # son manejadas por la app 'plantas'.
    path('', include('plantas.urls')),

    # --- Rutas de la API ---
    # Todas las rutas de la API (api/plantas, api/auth/register, etc.) están en 'plantas.api_urls'
    path('api/', include('plantas.api_urls')),

    # --- Rutas de Notificaciones y Google Calendar ---
    path('google-calendar/', include('notificaciones.urls')),
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/google-calendar-status/', GoogleCalendarStatusView.as_view(), name='google-calendar-status'),
    path('api/google-calendar-disconnect/', GoogleCalendarDisconnectView.as_view(), name='google-calendar-disconnect'),
    
]
