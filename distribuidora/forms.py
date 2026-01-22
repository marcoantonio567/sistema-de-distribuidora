from django import forms
from django.core.validators import RegexValidator

telefone_validator = RegexValidator(
    regex=r"^\+?\d{10,15}$",
    message="Informe um telefone válido com 10 a 15 dígitos."
)

class CheckoutForm(forms.Form):
    nome_cliente = forms.CharField(max_length=120)
    telefone = forms.CharField(max_length=20, validators=[telefone_validator])
    tipo_atendimento = forms.ChoiceField(choices=(("retirada","retirada"),("entrega","entrega")))
    rua = forms.CharField(max_length=120, required=False)
    numero = forms.CharField(max_length=10, required=False)
    bairro = forms.CharField(max_length=80, required=False)
    referencia = forms.CharField(max_length=120, required=False)
    observacoes = forms.CharField(max_length=255, required=False)
