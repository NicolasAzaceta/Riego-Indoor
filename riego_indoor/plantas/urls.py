from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlantaViewSet, RiegoViewSet, RegisterView, index_view, add_view #UsuarioViewSet
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from . import views


router = DefaultRouter()
#router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'plantas', PlantaViewSet, basename='plantas')
router.register(r'riegos', RiegoViewSet, basename='riegos')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
    path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
    path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
    # Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
    path('dashboard/', index_view, name='dashboard'),
    path('add/', add_view, name='add'),


]