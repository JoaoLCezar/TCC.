from django.shortcuts import render, redirect, get_object_or_404,get_list_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Categoria
from .forms import CategoriaForm
from django.core.paginator import Paginator
from core.decorators import group_required


@login_required
@group_required('Gerentes')
def listar_categorias(request):
    lista_de_categorias = Categoria.objects.all()

    # Paginação
    try:
        per_page = int(request.GET.get('per_page', 20))
    except (TypeError, ValueError):
        per_page = 20
    if per_page not in [10, 15, 20, 25, 30, 50]:
        per_page = 20
    paginator = Paginator(lista_de_categorias, per_page)  # categorias por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'categorias': page_obj,
        'lista_de_categorias': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'base_querystring': f"&per_page={per_page}",
        'page_size_options': [10, 15, 20, 25, 30, 50],
    }

    return render(request, 'categories/lista_categorias.html', contexto)


@login_required
@group_required('Gerentes')
def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria "{categoria.nome}" criada com sucesso!')
            return redirect('categories:listar_categorias')
        
    else:
        form = CategoriaForm()

    context = {
        'form':form
    }
    return render(request, 'categories/form_categoria.html', context)


@login_required
@group_required('Gerentes')
def atualizar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk = pk)

    if request.method =='POST':
        form = CategoriaForm(request.POST, instance=categoria)

        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria "{categoria.nome}" atualizada com sucesso!')
            return redirect('categories:listar_categorias')
        
    else:
        form = CategoriaForm(instance=categoria)

    context = {
        'form': form
    }
    return render(request, 'categories/form_categoria.html', context)


@login_required
@group_required('Gerentes')
def excluir_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk = pk)

    if request.method == 'POST':
        nome_categoria = categoria.nome
        categoria.delete()
        messages.success(request, f'Categoria "{nome_categoria}" excluída com sucesso!')
        return redirect('categories:listar_categorias') 

    context = {
        'categoria': categoria
    }   

    return render(request, 'categories/categoria_confirm_delete.html', context)

