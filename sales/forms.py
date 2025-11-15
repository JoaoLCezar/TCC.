from django import forms
from .models import SessaoCaixa


class SessaoCaixaForm(forms.ModelForm):
    class Meta:
        model = SessaoCaixa

        fields = ['valor_inicial']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['valor_inicial'].widget.attrs['class'] = 'form-control'
        self.fields['valor_inicial'].widget.attrs['placeholder'] = 'Ex: 150.00'
        

class SessaoCaixaFechamentoForm(forms.ModelForm):
    class Meta:
        model = SessaoCaixa

        fields = ['valor_final_informado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['valor_final_informado'].widget.attrs['class'] = 'form-control'
        self.fields['valor_final_informado'].widget.attrs['placeholder'] = 'Ex: 1150.50'
        self.fields['valor_final_informado'].label = "Valor Final Contado na Gaveta (R$)"