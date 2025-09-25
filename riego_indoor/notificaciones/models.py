# notificaciones/models.py
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL  # recommended, works si más adelante cambiás user model

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    calendar_id = models.CharField(max_length=255, blank=True, null=True,
                                   help_text='Email o ID del calendario donde crear eventos')

    def __str__(self):
        return f"Profile: {getattr(self.user, 'username', self.user)}"

