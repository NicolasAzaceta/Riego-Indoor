from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from .models import Planta, Riego, ConfiguracionUsuario

# -------- Configuración Indoor --------
class ConfiguracionUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para la configuración de ambiente indoor del usuario"""
    class Meta:
        model = ConfiguracionUsuario
        fields = ('id', 'temperatura_promedio', 'humedad_relativa')
        read_only_fields = ('id',)

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
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
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

    class Meta:
        model = Planta
        fields = (
            "id", "usuario", "nombre_personalizado", "tipo_planta",
            "tamano_planta", "tamano_maceta_litros", "fecha_ultimo_riego",
            "en_floracion",
            # calculados
            "recommended_water_ml", "frequency_days", "next_watering_date",
            "days_left", "estado_riego", "estado_texto", "sugerencia_suplementos",
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