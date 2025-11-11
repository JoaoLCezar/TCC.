from django import forms
from .models import Fornecedor

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor

        fields = [
            'nome_fantasia',
            'razao_social',
            'cnpj',
            'email',
            'telefone'
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
        self.fields['nome_fantasia'].widget.attrs['placeholder'] = 'Nome Comercial'
        self.fields['razao_social'].widget.attrs['placeholder'] = 'Razão Social (opcional)'
        self.fields['cnpj'].widget.attrs['placeholder'] = 'XX.XXX.XXX/0001-XX'
        self.fields['email'].widget.attrs['placeholder'] = 'contato@fornecedor.com'
        self.fields['telefone'].widget.attrs['placeholder'] = '(XX) XXXXX-XXXX'

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'