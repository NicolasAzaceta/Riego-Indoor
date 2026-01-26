from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (PlantaViewSet, RiegoViewSet, RegisterView, WeatherDataView, 
                    ConfiguracionUsuarioView, LocalidadUsuarioView, LocalidadClimaView, 
                    TriggerRecalculoOutdoorView)

router = DefaultRouter()
router.register(r'plantas', PlantaViewSet, basename='plantas')
router.register(r'riegos', RiegoViewSet, basename='riegos')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('weather/', WeatherDataView.as_view(), name='api-weather-data'),
    path('configuracion-usuario/', ConfiguracionUsuarioView.as_view(), name='configuracion-usuario'),
    path('localidad-outdoor/', LocalidadUsuarioView.as_view(), name='localidad-outdoor'),
    path('localidad-outdoor/clima/', LocalidadClimaView.as_view(), name='localidad-outdoor-clima'),
    path('recalcular-outdoor/', TriggerRecalculoOutdoorView.as_view(), name='recalcular-outdoor'),
    path('', include(router.urls)),
]