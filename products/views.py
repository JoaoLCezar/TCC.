from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from .models import Produto, MovimentoEstoque
from .forms import ProdutoForm, MovimentoEstoqueForm
from core.decorators import group_required


@login_required
@group_required('Gerentes')
def listar_produtos(request):
    
    produtos = Produto.objects.all().order_by('nome') #Puxa os objetos do banco e ordena por nome

    contexto = {
        'lista_de_produtos': produtos,
    }

    return render(request, 'products/lista_produtos.html', contexto)



@login_required
@group_required('Gerentes')
def detalhe_produto(request, pk):
    # Esta função busca um único produto no banco de dados pelo seu ID.
    # Se não for encontrado ela  retorna uma página de Erro 404.
    produto = get_object_or_404(Produto, pk=pk)

    if request.method == 'POST':
        form_estoque = MovimentoEstoqueForm(request.POST)

        if form_estoque.is_valid():
            try:
                with transaction.atomic():
                    movimento = form_estoque.save(commit=False)
                    movimento.produto = produto
                    movimento.usuario = request.user

                    nova_quantidade_estoque = produto.estoque + movimento.quantidade #atualiza o estoque

                    if nova_quantidade_estoque < 0:
                        messages.error(request, 'Erro: O estoque não pode ficar negativo.')
                    else:
                        produto.estoque = nova_quantidade_estoque

                        #Salva no banco de dados
                        produto.save()
                        movimento.save()

                        messages.success(request, f'Estoque de "{produto.nome}" atualizado com sucesso!')

                return redirect('products:detalhe_produto', pk=produto.pk)
            
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao atualizar o estoque: {e}')
    else:
        form_estoque = MovimentoEstoqueForm(initial={'tipo': 'ENTRADA'})

    contexto = {
        'produto': produto,
        'form_estoque': form_estoque,
    }

    return render(request, 'products/detalhe_produtos.html', contexto)


@login_required
@group_required('Gerentes')
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


@login_required
@group_required('Gerentes')
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
    
@login_required
@group_required('Gerentes')
def excluir_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)

    if request.method == 'POST':       
        produto.delete()

        return redirect('products:listar_produtos')
    
    context = {
        'produto': produto
    }
    return render(request, 'products/produto_confirm_delete.html', context)


@login_required
@group_required('Gerentes')
def historico_movimentos(request, pk):
    produto = get_object_or_404(Produto, pk=pk)

    movimentos = produto.movimentos.all()

    contexto = {
        'produto': produto,
        'movimentos': movimentos,
    }

    return render(request, 'products/historico_movimentos.html', contexto)