from django.shortcuts import render
from .models import Produto

# Create your views here.

def listar_produtos(request):
    
    produtos = Produto.objects.all().order_by('nome') #Puxa os objetos do banco e ordena por nome

    contexto = {
        'lista_de_produtos': produtos,
    }

    return render(request, 'products/lista_produtos.html', contexto)
