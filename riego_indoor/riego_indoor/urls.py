
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
#from django.http import HttpResponse
from plantas.views import home

# def home(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('home/', home, name='home'),
    #path('', home, name='home'),
    #path('home/dashboard/', index_view, name='dashboard'),
    
      # API principal
    path('api/', include('plantas.urls')),
    path('home/', include('plantas.urls')),
    path('api/', include('notificaciones.urls')),
    # JWT
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
]
