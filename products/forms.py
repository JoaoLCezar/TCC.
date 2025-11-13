from django import forms
from .models import Produto, MovimentoEstoque

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'preco', 'estoque', 'descricao']

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MovimentoEstoqueForm(forms.ModelForm):

    class Meta:
        model = MovimentoEstoque

        fields = ['quantidade', 'tipo', 'motivo']

        widgets = {
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: 50 ou -5'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Reposição, Ajuste'
            }),
        }    