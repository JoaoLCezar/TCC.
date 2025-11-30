from django import forms
from .models import Cliente
from .validators import is_valid_cpf, format_cpf, only_digits

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

    def clean_documento(self):
        doc = self.cleaned_data.get('documento')
        if not doc:
            return doc

        # Normalize and validate CPF
        if not is_valid_cpf(doc):
            raise forms.ValidationError('CPF inválido. Verifique e tente novamente.')

        # Store formatted CPF (human-readable)
        # Ensure no other cliente has the same CPF (ignoring formatting)
        normalized = only_digits(doc)
        qs = Cliente.objects.filter(documento__isnull=False).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None)
        for other in qs:
            if only_digits(other.documento) == normalized:
                raise forms.ValidationError('Já existe um cliente cadastrado com este CPF.')

        return format_cpf(doc)