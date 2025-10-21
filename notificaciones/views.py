from django.shortcuts import render, redirect
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth import login
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from datetime import datetime
from rest_framework.response import Response
from .services.google_calendar import get_oauth_flow
from .models import Profile
from django.contrib.auth.models import User

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Revertimos al comportamiento original:
        # Esta vista solo valida credenciales y devuelve tokens JWT.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


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
        return JsonResponse({'error': 'Token inválido o expirado'}, status=401)

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
    return redirect('/dashboard/')
