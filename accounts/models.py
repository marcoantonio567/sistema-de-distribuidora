from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

def validate_brazilian_phone(value: str):
    digits = ''.join(ch for ch in value if ch.isdigit())
    if len(digits) < 10 or len(digits) > 11:
        raise ValidationError('Telefone inválido. Informe DDD e número com 10 ou 11 dígitos.')

def validate_brazilian_cep(value: str):
    digits = ''.join(ch for ch in value if ch.isdigit())
    if len(digits) != 8:
        raise ValidationError('CEP inválido. Informe 8 dígitos.')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('Telefone', max_length=20, validators=[validate_brazilian_phone], blank=True)
    address_street = models.CharField('Rua', max_length=255, blank=True)
    address_number = models.CharField('Número', max_length=10, blank=True)
    address_complement = models.CharField('Complemento', max_length=50, blank=True)
    neighborhood = models.CharField('Bairro', max_length=100, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('Estado', max_length=2, blank=True)
    zip_code = models.CharField('CEP', max_length=9, validators=[validate_brazilian_cep], blank=True)

    def __str__(self):
        return f'{self.user.username}'
