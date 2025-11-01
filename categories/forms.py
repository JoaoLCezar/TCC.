from django import forms
from .models import Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria

        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['nome'].widget.attrs['class'] = 'form-control'

        self.fields['nome'].widget.attrs['placeholder'] = 'Ex: Bebidas, Limpeza, Doces, Padaria...'