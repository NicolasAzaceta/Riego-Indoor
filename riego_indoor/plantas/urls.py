from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlantaViewSet, RiegoViewSet, RegisterView #UsuarioViewSet

router = DefaultRouter()
#router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'plantas', PlantaViewSet, basename='plantas')
router.register(r'riegos', RiegoViewSet, basename='riegos')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),

]