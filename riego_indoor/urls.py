from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenRefreshView
from notificaciones.views import CustomTokenObtainPairView
from plantas.views import GoogleCalendarStatusView, GoogleCalendarDisconnectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Vistas de Páginas (Frontend) ---
    # La raíz del sitio ('') y otras rutas como /login, /register, /dashboard, etc.
    # son manejadas por la app 'plantas'.
    path('', include('plantas.urls')),

    # --- Django Auth URLs (para reseteo de contraseña y otras funciones) ---
    # Definimos explícitamente las rutas para sobreescribir las plantillas.
    path('accounts/password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html', subject_template_name='registration/password_reset_subject.txt'), 
         name='password_reset'),
    path('accounts/password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('accounts/reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
         name='password_reset_complete'),

    # Incluimos el resto de las URLs de auth por si se usan en el futuro.
    # Nuestras definiciones anteriores tienen prioridad.
    path('accounts/', include('django.contrib.auth.urls')),

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
