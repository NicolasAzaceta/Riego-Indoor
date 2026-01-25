from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlantaViewSet, RiegoViewSet, RegisterView, WeatherDataView, ConfiguracionUsuarioView

router = DefaultRouter()
router.register(r'plantas', PlantaViewSet, basename='plantas')
router.register(r'riegos', RiegoViewSet, basename='riegos')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('weather/', WeatherDataView.as_view(), name='api-weather-data'),
    path('configuracion-usuario/', ConfiguracionUsuarioView.as_view(), name='configuracion-usuario'),
    path('', include(router.urls)),
]