from django.shortcuts import render, redirect, get_object_or_404,get_list_or_404
from django.contrib.auth.decorators import login_required
from .models import Categoria
from .forms import CategoriaForm
from core.decorators import group_required


@login_required
@group_required('Gerentes')
def listar_categorias(request):
    categorias = Categoria.objects.all()

    contexto = {
        'lista_de_categorias': categorias,
    }

    return render(request, 'categories/lista_categorias.html', contexto)


@login_required
@group_required('Gerentes')
def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            form.save()

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
            form.save()

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
        categoria.delete()
        return redirect('categories:listar_categorias') 

    context = {
        'categoria': categoria
    }   

    return render(request, 'categories/categoria_confirm_delete.html', context)

