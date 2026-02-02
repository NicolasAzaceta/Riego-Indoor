from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings


class CookieTokenRefreshView(TokenRefreshView):
    """
    Vista personalizada para refresh que lee el token desde cookies
    y devuelve el nuevo access token también en cookies.
    """
    def post(self, request, *args, **kwargs):
        # Leer refresh token desde cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            raise InvalidToken('No se encontró refresh token')
        
        # Crear request data con el token de la cookie
        request.data['refresh'] = refresh_token
        
        # Llamar a la lógica estándar de SimpleJWT
        try:
            response = super().post(request, *args, **kwargs)
        except TokenError as e:
            raise InvalidToken(str(e))
        
        # Extraer el nuevo access token
        new_access = response.data.get('access')
        
        # Crear respuesta limpia
        clean_response = Response({'detail': 'Token refrescado exitosamente'})
        
        # Actualizar cookie de access token
        clean_response.set_cookie(
            key='access_token',
            value=new_access,
            max_age=3600,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        
        # Si hay rotación, también actualizar refresh token
        new_refresh = response.data.get('refresh')
        if new_refresh:
            clean_response.set_cookie(
                key='refresh_token',
                value=new_refresh,
                max_age=7*24*3600,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
        
        return clean_response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Cierra sesión del usuario:
        1. Agrega el refresh token al blacklist
        2. Borra las cookies del navegador
        """
        try:
            # Obtener refresh token de la cookie
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                # Agregar a blacklist
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Crear respuesta
            response = Response({
                'detail': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
            
            # Borrar cookies con los mismos parámetros que al crearlas
            response.delete_cookie(
                'access_token',
                path='/',
                samesite='Lax'
            )
            response.delete_cookie(
                'refresh_token',
                path='/',
                samesite='Lax'
            )
            
            return response
            
        except TokenError:
            # Si el token ya expiró o es inválido, igual limpiamos cookies
            response = Response({
                'detail': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
            response.delete_cookie(
                'access_token',
                path='/',
                samesite='Lax'
            )
            response.delete_cookie(
                'refresh_token',
                path='/',
                samesite='Lax'
            )
            return response
