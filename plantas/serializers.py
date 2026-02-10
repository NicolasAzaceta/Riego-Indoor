from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from .models import Planta, Riego, ConfiguracionUsuario, LocalidadUsuario, AuditLog, ImagenPlanta


# -------- Auditoría --------
class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de auditoría"""
    user_info = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = (
            'id', 'user', 'user_info', 'username', 'action', 'action_display',
            'timestamp', 'ip_address', 'user_agent', 'details'
        )
        read_only_fields = fields  # Todos los campos son read-only
    
    def get_user_info(self, obj):
        """Información básica del usuario si aún existe"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None


# -------- Configuración Indoor --------
class ConfiguracionUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para la configuración de ambiente indoor del usuario"""
    class Meta:
        model = ConfiguracionUsuario
        fields = ('id', 'temperatura_promedio', 'humedad_relativa')
        read_only_fields = ('id',)


# -------- Localidad Outdoor --------
class LocalidadUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para la localidad outdoor con recálculo automático"""
    class Meta:
        model = LocalidadUsuario
        fields = ('id', 'nombre_localidad', 'latitud', 'longitud', 'activo', 'ultima_actualizacion_clima')
        read_only_fields = ('id', 'ultima_actualizacion_clima')

# # -------- Usuarios --------Asi estaba creado por Nico. Lo modifico para ver si queda mejor con el profile oauth2
# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=6)

#     class Meta:
#         model = User
#         fields = ("id", "username", "email", "password")

#     def create(self, validated_data):
#         # crea usuario con contraseña hasheada
#         user = User.objects.create_user(
#             username=validated_data["username"],
#             email=validated_data.get("email", ""),
#             password=validated_data["password"],
#         )
#         return user
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Ya existe un usuario con esta dirección de correo electrónico.")]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

# -------- Riego --------
class RiegoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Riego
        fields = (
            "id", "planta", "fecha", "cantidad_agua_ml", "comentarios",
            "ph_agua", "ec_agua", "suplementos_aplicados"
        )
        read_only_fields = ("fecha",)


# -------- Imagen de Planta --------
class ImagenPlantaSerializer(serializers.ModelSerializer):
    """
    Serializer para imágenes de plantas almacenadas en GCS.
    Genera automáticamente Signed URLs frescas en cada request para bucket privado.
    """
    imagen_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImagenPlanta
        fields = ('id', 'imagen_url', 'gcs_blob_name', 'fecha_subida', 'orden')
        read_only_fields = ('id', 'gcs_blob_name', 'fecha_subida')
    
    def get_imagen_url(self, obj):
        """
        Genera una nueva Signed URL cada vez que se serializa la imagen.
        Esto asegura que las URLs siempre estén válidas.
        """
        try:
            from plantas.storage_service import PlantImageStorageService
            storage_service = PlantImageStorageService()
            return storage_service.generate_signed_url(obj.gcs_blob_name, expiration_days=7)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al generar signed URL para {obj.gcs_blob_name}: {e}")
            # Retornar None si falla (la imagen se mostrará como rota en frontend)
            return None


# -------- Planta --------
class PlantaSerializer(serializers.ModelSerializer):
    # Campos calculados (read-only) para que el front no haga cuentas
    recommended_water_ml = serializers.SerializerMethodField()
    frequency_days = serializers.SerializerMethodField()
    next_watering_date = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    estado_riego = serializers.SerializerMethodField()
    estado_texto = serializers.SerializerMethodField()
    sugerencia_suplementos = serializers.SerializerMethodField()
    imagenes = ImagenPlantaSerializer(many=True, read_only=True)

    class Meta:
        model = Planta
        fields = (
            "id", "usuario", "nombre_personalizado", "tipo_planta",
            "tamano_planta", "tipo_cultivo", "tamano_maceta_litros", "fecha_ultimo_riego",
            "en_floracion",
            # calculados
            "recommended_water_ml", "frequency_days", "next_watering_date",
            "days_left", "estado_riego", "estado_texto", "sugerencia_suplementos",
            # imágenes
            "imagenes",
        )
        read_only_fields = ("usuario",)

    def get_calc(self, obj):
        return obj.calculos_riego()

    def get_recommended_water_ml(self, obj): return self.get_calc(obj)["recommended_water_ml"]
    def get_frequency_days(self, obj): return self.get_calc(obj)["frequency_days"]
    def get_next_watering_date(self, obj): return self.get_calc(obj)["next_watering_date"]
    def get_days_left(self, obj): return self.get_calc(obj)["days_left"]
    def get_estado_riego(self, obj): return self.get_calc(obj)["estado_riego"]
    def get_estado_texto(self, obj): return self.get_calc(obj)["estado_texto"]
    def get_sugerencia_suplementos(self, obj): return self.get_calc(obj)["sugerencia_suplementos"]

    def create(self, validated_data):
        # setear dueño (usuario autenticado)
        user = self.context["request"].user
        validated_data["usuario"] = user
        return super().create(validated_data)