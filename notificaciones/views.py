from django.shortcuts import render, redirect
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth import login
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.response import Response
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from datetime import datetime
from .services.google_calendar import get_oauth_flow
from .models import Profile
from django.contrib.auth.models import User

@method_decorator(ratelimit(key='ip', rate='10/h', method='POST'), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Obtener tokens del serializador estándar
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data
        
        # Crear respuesta sin tokens en el body
        response = Response({
            'detail': 'Login exitoso',
            'username': request.data.get('username')
        })
        
        # Configurar cookies httpOnly con los tokens
        response.set_cookie(
            key='access_token',
            value=tokens['access'],
            max_age=3600,  # 1 hora (igual que ACCESS_TOKEN_LIFETIME)
            httponly=True,
            secure=not settings.DEBUG,  # True en producción (HTTPS)
            samesite='Lax'
        )
        
        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh'],
            max_age=7*24*3600,  # 7 días (igual que REFRESH_TOKEN_LIFETIME)
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        
        return response


def google_calendar_auth(request):
    """
    Inicia el flujo de OAuth. Recibe el token JWT como parámetro en la URL.
    """
    jwt_token = request.GET.get('jwt')
    if not jwt_token:
        return JsonResponse({'error': 'Token no proporcionado'}, status=401)

    try:
        # Validamos el token y obtenemos el usuario
        token = AccessToken(jwt_token)
        user_id = token.payload.get('user_id')
        user = User.objects.get(id=user_id)
        login(request, user) # Iniciamos una sesión de Django para este usuario
    except Exception as e:
        print(f"DEBUG AUTH ERROR: {str(e)}")
        print(f"DEBUG TOKEN: {jwt_token}")
        return JsonResponse({'error': f'Token inválido o expirado: {str(e)}'}, status=401)

    flow = get_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # <-- AÑADIDO: Esto fuerza a Google a emitir un nuevo refresh_token
    )
    request.session['oauth_state'] = state
    return redirect(authorization_url)


def google_calendar_callback(request):
    """
    Callback de Google. El usuario ya está autenticado por la sesión de Django.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Usuario no autenticado en la sesión'}, status=401)

    flow = get_oauth_flow()
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.google_access_token = credentials.token
    profile.google_refresh_token = credentials.refresh_token
    profile.google_token_expiry = credentials.expiry
    profile.save()
    
    # --- NUEVO: Rellenar eventos faltantes en background ---
    import threading
    from .services.google_calendar import populate_missing_events
    
    def run_population(user_inst):
        try:
            print(f"Iniciando población de eventos para {user_inst.username}...")
            count, errs = populate_missing_events(user_inst)
            print(f"Población finalizada: {count} eventos creados, {len(errs)} errores.")
        except Exception as e:
            print(f"Error en thread de población: {e}")

    t = threading.Thread(target=run_population, args=(request.user,))
    t.daemon = True
    t.start()
    
    return redirect('/dashboard/')
