from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Produto, MovimentoEstoque
from categories.models import Categoria
from .forms import ProdutoForm, MovimentoEstoqueForm
from core.decorators import group_required


@login_required
@group_required('Gerentes')
def listar_produtos(request):
    categoria_id = request.GET.get('categoria')

    produtos_qs = Produto.objects.select_related('categoria').filter(ativo=True)
    if categoria_id and categoria_id.isdigit():
        produtos_qs = produtos_qs.filter(categoria_id=categoria_id)

    produtos_qs = produtos_qs.order_by('categoria__nome', 'nome') # Ordena por categoria e nome

    # Paginação
    try:
        per_page = int(request.GET.get('per_page', 15))
    except (TypeError, ValueError):
        per_page = 15
    if per_page not in [10, 15, 20, 25, 30, 50]:
        per_page = 15
    paginator = Paginator(produtos_qs, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categorias disponíveis (com produtos)
    categorias_disponiveis = (
        Produto.objects.select_related('categoria')
        .exclude(categoria__isnull=True)
        .values('categoria_id', 'categoria__nome')
        .order_by('categoria__nome')
        .distinct()
    )

    # Base querystring para paginação
    qs_parts = []
    if categoria_id and categoria_id.isdigit():
        qs_parts.append(f"categoria={categoria_id}")
    qs_parts.append(f"per_page={per_page}")
    base_querystring = "&" + "&".join(qs_parts) if qs_parts else ""

    contexto = {
        'lista_de_produtos': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'base_querystring': base_querystring,
        'page_size_options': [10, 15, 20, 25, 30, 50],
        'categorias_filtro': list(categorias_disponiveis),
        'categoria_selecionada': int(categoria_id) if categoria_id and categoria_id.isdigit() else None,
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
            produto = form.save()
            messages.success(request, f'Produto "{produto.nome}" cadastrado com sucesso!')
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
            produto = form.save()
            messages.success(request, f'Produto "{produto.nome}" atualizado com sucesso!')
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
        acao = request.POST.get('acao', 'excluir')
        if acao == 'desativar':
            produto.ativo = False
            produto.save()
            messages.success(request, f'Produto "{produto.nome}" desativado com sucesso!')
            return redirect('products:listar_produtos')

        # ação padrão: excluir
        try:
            nome_produto = produto.nome
            produto.delete()
            messages.success(request, f'Produto "{nome_produto}" excluído com sucesso!')
            return redirect('products:listar_produtos')
        except ProtectedError as e:
            # Há referências protegidas (ex: ItemVenda) — notificar e oferecer desativação
            protected = getattr(e, 'protected_objects', None)
            count = len(protected) if protected is not None else 'várias'
            messages.error(request, (
                f'Não foi possível excluir "{produto.nome}" porque ele é referenciado por {count} registro(s) de venda.'
                ' Você pode desativar o produto em vez de excluí-lo.'
            ))
            return redirect('products:detalhe_produto', pk=produto.pk)
    
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