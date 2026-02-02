from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTCookieAuthentication(JWTAuthentication):
    """
    Autenticación JWT que primero intenta leer el token desde cookies,
    y si no está, usa el header Authorization (para compatibilidad).
    """
    def authenticate(self, request):
        # Primero intentar desde cookie
        cookie_token = request.COOKIES.get('access_token')
        
        if cookie_token:
            # Validar token desde cookie
            validated_token = self.get_validated_token(cookie_token)
            return self.get_user(validated_token), validated_token
        
        # Si no hay cookie, intentar desde header (compatibilidad/testing)
        return super().authenticate(request)
