from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from .models import Planta, Riego
from .serializers import PlantaSerializer, RiegoSerializer, RegisterSerializer
from .permissions import IsOwner

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate


def home(request):
    return render(request, 'login.html')

def index_view(request):
    return render(request, 'index.html')

def add_view(request):
    return render(request, 'add-plants.html')

def detail_view(request):
    return render(request, 'detail.html')

# -------- Registro de usuarios --------
from rest_framework.views import APIView

class RegisterView(APIView):
    permission_classes = []  # cualquiera puede registrarse
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"id": user.id, "username": user.username}, status=status.HTTP_201_CREATED)


# -------- Plantas --------
class PlantaViewSet(viewsets.ModelViewSet):
    serializer_class = PlantaSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Cada usuario sólo ve sus plantas
        return Planta.objects.filter(usuario=self.request.user).order_by("id")

    def perform_create(self, serializer):
        serializer.save()  # el serializer setea usuario desde request

    @action(detail=True, methods=['get'])
    def estado(self, request, pk=None):
        planta = self.get_object()
        datos = planta.calculos_riego()
        return Response(datos)

    @action(detail=True, methods=['post'])
    def regar(self, request, pk=None):
        """
        Crea un registro de riego para esta planta y actualiza fecha_ultimo_riego.
        Body opcional: { "cantidad_agua_ml": 800, "comentarios": "Riego liviano" }
        """
        planta = self.get_object()
        data = {
            "planta": planta.id,
            "cantidad_agua_ml": request.data.get("cantidad_agua_ml"),
            "comentarios": request.data.get("comentarios", ""),
        }
        serializer = RiegoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        riego = serializer.save()
        return Response(RiegoSerializer(riego).data, status=status.HTTP_201_CREATED)


# -------- Riegos --------
class RiegoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Sólo lectura global, pero filtrable por ?planta=<id>.
    Para crear riegos usá la acción POST /plantas/{id}/regar/
    """
    serializer_class = RiegoSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = Riego.objects.select_related("planta", "planta__usuario").all().order_by("-fecha", "-id")
        qs = [r for r in qs if r.planta.usuario == self.request.user]
        planta_id = self.request.query_params.get("planta")
        if planta_id:
            qs = [r for r in qs if str(r.planta_id) == str(planta_id)]
        # Convertimos a queryset-like (lista está bien para ReadOnly con DRF, pero si querés queryset real, usá filtrado por ORM)
        from django.db.models.query import QuerySet
        return qs  # DRF acepta iterables; si preferís, cambiamos el enfoque a ORM puro.


# -------- Usuarios --------
# class UserViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = User.objects.all().order_by("id")
#     serializer_class = RegisterSerializer
#     permission_classes = [IsAuthenticated]  # Sólo usuarios autenticados pueden ver la lista de usuarios

#     @action(detail=False, methods=['get'])
#     def me(self, request):
#         serializer = self.get_serializer(request.user)
#         return Response(serializer.data)
    
# Nota: para login/logout usá las vistas de rest_framework.urls o JWT.

# o HttpResponse("Bienvenido a la API de Riego Indoor")
# Alternativamente, podés usar HttpResponse si no querés template.
# Y en urls.py, mapeá la vista home_view a la ruta raíz o /home/ según prefieras.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):   
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
# Alternativamente, podés usar HttpResponse si no querés template.
# from django.http import HttpResponse
# def home_view(request):
#     return HttpResponse("Bienvenido a la API de Riego Indoor")
# Luego en urls.py:
# path('home/', home_view, name='home'),
# path('', home_view, name='home'),  # si querés que sea la raíz
# O podés usar TemplateView directamente en urls.py si no necesitás lógica adicional.
# from django.views.generic import TemplateView
# path('home/', TemplateView.as_view(template_name='login.html'), name='home'),
# path('', TemplateView.as_view(template_name='login.html'), name='home'),  # si querés que sea la raíz
# Asegurate de tener el template login.html en la carpeta templates y la configuración correcta en settings.py
