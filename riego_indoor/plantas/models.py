from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

class Planta(models.Model):
    TIPO_PLANTA_CHOICES = [
        ('auto', 'Autofloreciente'),
        ('foto', 'Fotoperiódica'),
    ]
    TAMANO_CHOICES = [
        ('pequeña', 'Pequeña'),
        ('mediana', 'Mediana'),
        ('grande', 'Grande'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_personalizado = models.CharField(max_length=100)
    tipo_planta = models.CharField(max_length=10, choices=TIPO_PLANTA_CHOICES)
    tamano_planta = models.CharField(max_length=10, choices=TAMANO_CHOICES)
    tamano_maceta_litros = models.FloatField(help_text="Tamaño en litros")
    fecha_ultimo_riego = models.DateField()
    en_floracion = models.BooleanField(default=False)

    # ---------- LÓGICA DE CÁLCULO ----------
    def calculos_riego(self):
       
        litros = max(self.tamano_maceta_litros or 0, 0)
        size = self.tamano_planta
        en_flor = self.en_floracion

        # Heurística simple y prudente:
        # Volumen por riego ≈ 15% del volumen de maceta (veg) y ≈ 20% (flor)
        porcentaje = 0.20 if en_flor else 0.15
        recommended_water_ml = int(litros * 1000 * porcentaje)

        # Frecuencia base ~ litros/2 días (10L ≈ 5 días)
        # Ajustes por tamaño de planta y floración
        base = litros / 2.0  # p.ej., 12L -> 6 días
        size_offset = {'pequeña': -1.0, 'mediana': 0.0, 'grande': 1.0}.get(size, 0.0)
        stage_offset = -1.0 if en_flor else 0.0
        frequency_days = int(max(2, min(7, round(base + size_offset + stage_offset, 0))))

        next_watering_date = self.fecha_ultimo_riego + timedelta(days=frequency_days)
        today = date.today()
        days_left = (next_watering_date - today).days

        if days_left > 1:
            estado_riego = 'no_necesita'
            estado_texto = 'No necesita agua'
        elif 0 < days_left <= 1:
            estado_riego = 'pronto'
            estado_texto = 'Pronto a regar'
        else:
            estado_riego = 'hoy'
            estado_texto = 'Necesita riego hoy'

        # Sugerencia genérica y conservadora de suplementos (si los usan).
        # SIEMPRE empezar con dosis bajas y respetar etiqueta de cada marca.
        if en_flor:
            sugerencia = "Floración: Base Bloom ~1 ml/L + Cal-Mag ~0.5 ml/L (arrancar bajo). Ajustar pH según sustrato."
        else:
            sugerencia = "Vegetación: Base Grow ~1 ml/L + Cal-Mag ~0.5 ml/L (arrancar bajo). Ajustar pH según sustrato."

        return {
            "recommended_water_ml": recommended_water_ml,
            "frequency_days": frequency_days,
            "next_watering_date": next_watering_date,
            "days_left": days_left,
            "estado_riego": estado_riego,
            "estado_texto": estado_texto,
            "sugerencia_suplementos": sugerencia,
        }

    def __str__(self):
        return f"{self.nombre_personalizado} ({self.usuario.username})"

class Riego(models.Model):
    planta = models.ForeignKey(Planta, on_delete=models.CASCADE, related_name='riegos')
    fecha = models.DateField(auto_now_add=True)
    cantidad_agua_ml = models.IntegerField(null=True, blank=True)
    comentarios = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # actualizar último riego de la planta automáticamente a la fecha de este riego
        if self.planta.fecha_ultimo_riego is None or self.fecha >= self.planta.fecha_ultimo_riego:
            self.planta.fecha_ultimo_riego = self.fecha
            self.planta.save(update_fields=['fecha_ultimo_riego'])

    def __str__(self):
        return f"Riego {self.planta.nombre_personalizado} - {self.fecha}"
