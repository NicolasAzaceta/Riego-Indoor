from django.contrib import admin
from .models import Planta, Riego


@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "nombre_personalizado", "tipo_planta", "tamano_planta",
                    "tamano_maceta_litros", "fecha_ultimo_riego", "en_floracion")

@admin.register(Riego)
class RiegoAdmin(admin.ModelAdmin):
    list_display = ("id", "planta", "fecha", "cantidad_agua_ml")