from django.shortcuts import render, get_object_or_404, redirect
from .models import Produto
from .forms import ProdutoForm

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

def criar_produto(request):
    if request.method =='POST':
        form = ProdutoForm(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('products:listar_produtos')
            
    else:
        form = ProdutoForm()

    context = {
            'form': form
        }
    return render(request, 'products/form_produtos.html', context)


def atualizar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)

    if request.method =='POST':
        form = ProdutoForm(request.POST, instance=produto)

        if form.is_valid():
            form.save()

            return redirect('products:detalhe_produto', pk=produto.pk)
        
    else:
        form = ProdutoForm(instance=produto)

    context = {
        'form': form
    }
    return render(request, 'products/form_produtos.html', context)
    
