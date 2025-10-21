from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """
    Permite acceso sólo si el objeto pertenece al usuario autenticado.
    """

    def has_object_permission(self, request, view, obj):
        # obj puede ser Planta o Riego; en Riego el dueño es obj.planta.usuario
        owner = getattr(obj, "usuario", None) or getattr(getattr(obj, "planta", None), "usuario", None)
        return owner == request.user