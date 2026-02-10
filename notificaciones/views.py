from django.shortcuts import render, redirect
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth import login
import logging
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
from plantas.models import AuditLog
from plantas.authentication import JWTCookieAuthentication # Importamos autenticación por cookie

# Logger para este módulo
logger = logging.getLogger(__name__)

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
        
        # Registrar auditoría de login
        try:
            user = User.objects.get(username=request.data.get('username'))
            AuditLog.log(user, 'LOGIN', request)
            logger.info(f"Login exitoso: {user.username}")
        except User.DoesNotExist:
            logger.warning(f"Intento de login con usuario inexistente: {request.data.get('username')}")
        
        return response


def google_calendar_auth(request):
    """
    Inicia el flujo de OAuth. Intenta autenticar por cookie HttpOnly primero.
    Si falla, intenta por parámetro URL (legacy/fallback).
    """
    user = None
    
    # 1. Intentar autenticación por Cookie (Lo estándar ahora)
    try:
        auth = JWTCookieAuthentication()
        user_auth = auth.authenticate(request)
        if user_auth:
            user = user_auth[0]
            login(request, user)
            logger.info(f"Usuario {user.username} autenticado vía Cookie para Google Calendar")
    except Exception as e:
        logger.warning(f"Fallo auth por cookie en Google Calendar: {e}")

    # 2. Si no funcionó, intentar por parámetro JWT (Legacy)
    if not user:
        jwt_token = request.GET.get('jwt')
        if jwt_token:
            try:
                token = AccessToken(jwt_token)
                user_id = token.payload.get('user_id')
                user = User.objects.get(id=user_id)
                login(request, user)
                logger.info(f"Usuario {user.username} autenticado vía Param JWT para Google Calendar")
            except Exception as e:
                logger.error(f"Error en autenticación por param JWT: {str(e)}")
                return JsonResponse({'error': f'Token inválido o expirado: {str(e)}'}, status=401)

    # 3. Si sigue sin usuario, error
    if not user:
         if request.user.is_authenticated:
             # Si ya venía autenticado por sesión de Django (raro pero posible)
             user = request.user
         else:
             return JsonResponse({'error': 'No se pudo autenticar al usuario. Inicie sesión nuevamente.'}, status=401)

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
    
    # Registrar auditoría
    AuditLog.log(request.user, 'CALENDAR_LINK', request)
    logger.info(f"Google Calendar vinculado para usuario: {request.user.username}")
    
    # --- NUEVO: Rellenar eventos faltantes en background ---
    import threading
    from .services.google_calendar import populate_missing_events
    
    def run_population(user_inst):
        try:
            logger.info(f"Iniciando población de eventos de calendar para {user_inst.username}")
            count, errs = populate_missing_events(user_inst)
            logger.info(f"Población finalizada para {user_inst.username}: {count} eventos creados, {len(errs)} errores")
        except Exception as e:
            logger.error(f"Error en población de eventos para {user_inst.username}: {e}")

    t = threading.Thread(target=run_population, args=(request.user,))
    t.daemon = True
    t.start()
    
    return redirect('/dashboard/')
