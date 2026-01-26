from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

def validate_brazilian_phone(value: str):
    digits = ''.join(ch for ch in value if ch.isdigit())
    if len(digits) < 10 or len(digits) > 11:
        raise ValidationError('Telefone inválido. Informe DDD e número com 10 ou 11 dígitos.')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('Telefone', max_length=20, validators=[validate_brazilian_phone], blank=True)

    def __str__(self):
        return f'{self.user.username}'
