from django import forms
from .models import Produto, MovimentoEstoque

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'codigo_barras', 'categoria', 'preco_custo', 'preco', 'estoque', 'descricao']

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 7891234567890'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'preco_custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
        labels = {
            'nome': 'Nome do Produto',
            'codigo_barras': 'Código de Barras (EAN-13, EAN-8, etc.)',
            'categoria': 'Categoria',
            'preco_custo': 'Preço de Custo (R$)',
            'preco': 'Preço de Venda (R$)',
            'estoque': 'Quantidade em Estoque',
            'descricao': 'Descrição',
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