from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta, date


class AuditLog(models.Model):
    """
    Registro de auditoría para acciones críticas de usuario.
    Permite trazabilidad completa de operaciones importantes en el sistema.
    """
    ACTION_CHOICES = [
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('REGISTER', 'Registro de usuario'),
        ('DELETE_ACCOUNT', 'Eliminación de cuenta'),
        ('CALENDAR_LINK', 'Vinculación de Google Calendar'),
        ('CALENDAR_UNLINK', 'Desvinculación de Google Calendar'),
        ('PLANT_CREATE', 'Creación de planta'),
        ('PLANT_DELETE', 'Eliminación de planta'),
        ('CONFIG_UPDATE', 'Actualización de configuración'),
        ('PASSWORD_CHANGE', 'Cambio de contraseña'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs',
        help_text="Usuario que realizó la acción (null si fue eliminado)"
    )
    username = models.CharField(
        max_length=150,
        help_text="Nombre de usuario (guardado por si el usuario se elimina)"
    )
    action = models.CharField(
        max_length=50, 
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Tipo de acción realizada"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Momento en que ocurrió la acción"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="Dirección IP desde donde se realizó la acción"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User-Agent del navegador"
    )
    details = models.JSONField(
        null=True, 
        blank=True,
        help_text="Detalles adicionales de la acción en formato JSON"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log(cls, user, action, request=None, details=None):
        """
        Helper method to create audit log entries easily.
        
        Args:
            user: User instance or None
            action: One of the ACTION_CHOICES keys
            request: Django request object (optional, for IP and User-Agent)
            details: Dict with additional information (optional)
        
        Returns:
            Created AuditLog instance
        """
        from plantas.utils.logging_helpers import get_client_ip, get_user_agent
        
        log_entry = cls(
            user=user,
            username=user.username if user else 'anonymous',
            action=action,
            details=details
        )
        
        if request:
            log_entry.ip_address = get_client_ip(request)
            log_entry.user_agent = get_user_agent(request)
        
        log_entry.save()
        return log_entry


class ConfiguracionUsuario(models.Model):
    """
    Configuración de ambiente indoor del usuario.
    Un usuario tiene una configuración que se aplica a todas sus plantas indoor.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuracion_cultivo')
    temperatura_promedio = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-10.0), MaxValueValidator(50.0)],
        help_text="Temperatura promedio del espacio de cultivo indoor (°C). Rango: -10 a 50°C"
    )
    humedad_relativa = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Humedad relativa promedio del espacio de cultivo indoor (%). Rango: 0-100%"
    )
    
    class Meta:
        verbose_name = "Configuración de Usuario"
        verbose_name_plural = "Configuraciones de Usuarios"
    
    def __str__(self):
        return f"Config de {self.user.username}"


class LocalidadUsuario(models.Model):
    """
    Localidad seleccionada para plantas outdoor con recálculo automático.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='localidad_outdoor')
    nombre_localidad = models.CharField(max_length=255, help_text="Ej: Córdoba, Argentina")
    latitud = models.FloatField(help_text="Latitud de la localidad")
    longitud = models.FloatField(help_text="Longitud de la localidad")
    activo = models.BooleanField(default=True, help_text="Si está activo, recalcula riegos automáticamente")
    ultima_actualizacion_clima = models.DateTimeField(null=True, blank=True, help_text="Última vez que se obtuvo el clima")
    
    class Meta:
        verbose_name = "Localidad de Usuario"
        verbose_name_plural = "Localidades de Usuarios"
    
    def __str__(self):
        return f"{self.user.username} - {self.nombre_localidad}"


class RegistroClima(models.Model):
    """
    Registro histórico de clima para análisis y recálculo de riegos.
    """
    localidad = models.ForeignKey(LocalidadUsuario, on_delete=models.CASCADE, related_name='registros_clima')
    fecha = models.DateField(auto_now_add=True)
    
    # Datos meteorológicos
    temperatura_max = models.FloatField(help_text="Temperatura máxima del día (°C)")
    temperatura_min = models.FloatField(help_text="Temperatura mínima del día (°C)")
    humedad_promedio = models.FloatField(help_text="Humedad relativa promedio (%)")
    precipitacion_mm = models.FloatField(default=0, help_text="Precipitación en milímetros")
    velocidad_viento_kmh = models.FloatField(default=0, help_text="Velocidad del viento (km/h)")
    
    # Control de procesamiento
    riegos_recalculados = models.BooleanField(default=False, help_text="Si ya se procesó este registro")
    
    class Meta:
        unique_together = ['localidad', 'fecha']
        ordering = ['-fecha']
        verbose_name = "Registro de Clima"
        verbose_name_plural = "Registros de Clima"
    
    def __str__(self):
        return f"{self.localidad.nombre_localidad} - {self.fecha}"



class Planta(models.Model):
    TIPO_PLANTA_CHOICES = [
        ('Auto', 'Autofloreciente',),
        ('Foto', 'Fotoperiódica'),
    ]
    TAMANO_CHOICES = [
        ('Pequeña', 'Pequeña'),
        ('Mediana', 'Mediana'),
        ('Grande', 'Grande'),
    ]
    TIPO_CULTIVO_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_personalizado = models.CharField(max_length=100)
    tipo_planta = models.CharField(max_length=10, choices=TIPO_PLANTA_CHOICES)
    tamano_planta = models.CharField(max_length=10, choices=TAMANO_CHOICES)
    tipo_cultivo = models.CharField(
        max_length=10, 
        choices=TIPO_CULTIVO_CHOICES, 
        default='indoor',
        help_text="Tipo de cultivo: indoor (temp/humedad fijas) u outdoor (clima automático)"
    )
    tamano_maceta_litros = models.FloatField(validators=[MinValueValidator(0.1)], help_text="Tamaño en litros (mínimo 0.1L)")
    fecha_ultimo_riego = models.DateField()
    en_floracion = models.BooleanField(default=False)
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID del evento de Google Calendar para el próximo riego")

    # ---------- LÓGICA DE CÁLCULO ----------
    def calculos_riego(self, temperatura_externa=None, humedad_externa=None):
        """
        Calcula días restantes, cantidad de agua, y estado de riego.
        Ajusta según temperatura y humedad externas (si se proporcionan).
        """
        litros = max(self.tamano_maceta_litros, 0.1)  # Mínimo 0.1L
        size = self.tamano_planta
        en_flor = self.en_floracion

        # Heurística mejorada:
        # Volumen por riego ≈ 15% del volumen de maceta (veg) y ≈ 20% (flor)
        porcentaje = 0.20 if en_flor else 0.15
        recommended_water_ml = int(litros * 1000 * porcentaje)
        
        # Límite máximo de agua por riego: 5000ml (5L)
        recommended_water_ml = min(recommended_water_ml, 5000)

        # Frecuencia base ~ litros/2 días (10L ≈ 5 días)
        # Ajustes por tamaño de planta, floración, temperatura y humedad
        base = litros / 2.0 if litros > 0 else 2.0  # p.ej., 12L -> 6 días
        
        # Ajuste por tamaño de planta
        size_map = {'Pequeña': -1.0, 'pequeña': -1.0, 'Mediana': 0.0, 'mediana': 0.0, 'Grande': 1.0, 'grande': 1.0}
        size_offset = size_map.get(size, 0.0)
        
        # Ajuste por relación planta/maceta (planta grande en maceta pequeña necesita más riego)
        ratio_offset = 0.0
        if size in ['Grande', 'grande'] and litros < 10:
            ratio_offset = -1.0  # Regar más seguido
        elif size in ['Pequeña', 'pequeña'] and litros > 15:
            ratio_offset = 0.5   # Regar menos seguido
        
        # Ajuste por etapa de floración
        stage_offset = -1.0 if en_flor else 0.0
        
        # Ajuste por temperatura (gradual con 6 niveles)
        temp_offset = 0.0
        if temperatura_externa is not None:
            if temperatura_externa > 30:
                temp_offset = -2.0  # Muy caliente, regar mucho más seguido
            elif temperatura_externa > 28:
                temp_offset = -1.0  # Caliente, regar más seguido
            elif temperatura_externa > 25:
                temp_offset = -0.5  # Templado-caliente, regar un poco más seguido
            elif temperatura_externa < 12:
                temp_offset = 2.0   # Muy frío, regar mucho menos seguido
            elif temperatura_externa < 15:
                temp_offset = 1.0   # Frío, regar menos seguido
            elif temperatura_externa < 18:
                temp_offset = 0.5   # Templado-frío, regar un poco menos seguido

        # Ajuste por humedad relativa (humedad baja → más transpiración → más riego)
        humedad_offset = 0.0
        if humedad_externa is not None:
            if humedad_externa < 30:
                humedad_offset = -1.0  # Muy seco, regar más seguido
            elif humedad_externa < 40:
                humedad_offset = -0.5  # Seco, regar un poco más seguido
            elif humedad_externa > 70:
                humedad_offset = 1.0   # Muy húmedo, regar menos seguido
            elif humedad_externa > 60:
                humedad_offset = 0.5   # Húmedo, regar un poco menos seguido

        # Cálculo final de frecuencia
        frequency_days = int(max(2, min(7, round(
            base + size_offset + ratio_offset + stage_offset + temp_offset + humedad_offset, 0
        ))))

        next_watering_date = self.fecha_ultimo_riego + timedelta(days=frequency_days)
        today = date.today()
        days_left = (next_watering_date - today).days

        # Estados de riego mejorados con "urgente"
        if days_left > 1:
            estado_riego = 'no_necesita'
            estado_texto = 'No necesita agua'
        elif days_left == 1:
            estado_riego = 'pronto'
            estado_texto = 'Pronto a regar'
        elif days_left == 0:
            estado_riego = 'hoy'
            estado_texto = 'Necesita riego hoy'
        else:  # days_left < 0
            estado_riego = 'urgente'
            estado_texto = f'Riego urgente (atrasado {abs(days_left)} día{"s" if abs(days_left) > 1 else ""})'

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
    
    # Campos de tracking avanzado
    ph_agua = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(14.0)],
        help_text="pH del agua (rango 0-14)"
    )
    ec_agua = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Conductividad eléctrica del agua (mS/cm)"
    )
    suplementos_aplicados = models.TextField(
        blank=True,
        help_text="Descripción de suplementos/nutrientes aplicados"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # actualizar último riego de la planta automáticamente a la fecha de este riego
        if self.planta.fecha_ultimo_riego is None or self.fecha >= self.planta.fecha_ultimo_riego:
            self.planta.fecha_ultimo_riego = self.fecha
            self.planta.save(update_fields=['fecha_ultimo_riego'])

    def __str__(self):
        return f"Riego {self.planta.nombre_personalizado} - {self.fecha}"


class ImagenPlanta(models.Model):
    """
    Modelo para almacenar imágenes de plantas en Google Cloud Storage.
    Permite a los usuarios subir múltiples fotos de cada planta.
    """
    planta = models.ForeignKey(
        Planta,
        on_delete=models.CASCADE,
        related_name='imagenes',
        help_text="Planta a la que pertenece esta imagen"
    )
    imagen_url = models.URLField(
        max_length=500,
        help_text="URL pública de la imagen en Google Cloud Storage"
    )
    gcs_blob_name = models.CharField(
        max_length=255,
        help_text="Nombre del blob en GCS (para eliminación)",
        db_index=True
    )
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de subida de la imagen"
    )
    orden = models.IntegerField(
        default=0,
        help_text="Orden de visualización en la galería"
    )
    
    class Meta:
        ordering = ['orden', '-fecha_subida']
        verbose_name = "Imagen de Planta"
        verbose_name_plural = "Imágenes de Plantas"
        indexes = [
            models.Index(fields=['planta', 'orden']),
            models.Index(fields=['planta', '-fecha_subida']),
        ]
    
    def __str__(self):
        return f"Imagen {self.id} de {self.planta.nombre_personalizado}"
