"""
ViewSets adicionales para la app plantas
"""
from rest_framework import viewsets, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consultar logs de auditoría.
    Los usuarios solo pueden ver sus propios logs.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar logs solo del usuario autenticado"""
        return AuditLog.objects.filter(user=self.request.user)
