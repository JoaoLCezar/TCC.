from django.shortcuts import render, get_object_or_404
from .models import Produto

# Create your views here.

def listar_produtos(request):
    
    produtos = Produto.objects.all().order_by('nome') #Puxa os objetos do banco e ordena por nome

    contexto = {
        'lista_de_produtos': produtos,
    }

    return render(request, 'products/lista_produtos.html', contexto)

def detalhe_produto(request, pk):
    # Esta função busca um único produto no banco de dados pelo seu ID.
    # Se não for encontrado ela  retorna uma página de Erro 404.
    produto = get_object_or_404(Produto, pk=pk)

    contexto ={
        'produto' : produto
    }
    return render(request, 'products/detalhe_produtos.html', contexto)
