from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta: 
        model = Cliente

        fields = ['nome', 'email', 'telefone', 'documento']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['nome'].widget.attrs['placeholder'] = 'Nome completo do cliente'
        self.fields['email'].widget.attrs['placeholder'] = 'email@exemplo.com'
        self.fields['telefone'].widget.attrs['placeholder'] = '(21) 99999-8888'
        self.fields['documento'].widget.attrs['placeholder'] = 'CPF'

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'