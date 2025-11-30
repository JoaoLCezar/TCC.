from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Fornecedor
from .forms import FornecedorForm
from core.decorators import group_required


@login_required
@group_required('Gerentes')
def listar_fornecedores(request):
    lista_de_fornecedores = Fornecedor.objects.all()

    # Paginação
    try:
        per_page = int(request.GET.get('per_page', 20))
    except (TypeError, ValueError):
        per_page = 20
    if per_page not in [10, 15, 20, 25, 30, 50]:
        per_page = 20
    paginator = Paginator(lista_de_fornecedores, per_page)  # fornecedores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'fornecedores': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'base_querystring': f"&per_page={per_page}",
        'page_size_options': [10, 15, 20, 25, 30, 50],
    }

    return render(request, 'suppliers/lista_fornecedores.html', contexto)


@login_required
@group_required('Gerentes')
def criar_fornecedor(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)

        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, f'Fornecedor "{fornecedor.nome_fantasia}" cadastrado com sucesso!')
            return redirect('suppliers:listar_fornecedores')
        
    else:
        form = FornecedorForm()
    
    contexto = {
        'form': form
    }

    return render(request, 'suppliers/form_fornecedor.html', contexto)

@login_required
@group_required('Gerentes')
def atualizar_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)

        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, f'Fornecedor "{fornecedor.nome_fantasia}" atualizado com sucesso!')
            return redirect('suppliers:listar_fornecedores')
        
    else:
        form = FornecedorForm(instance=fornecedor)

    contexto = {
        'form': form
    }
    return render(request, 'suppliers/form_fornecedor.html', contexto)


@login_required
@group_required('Gerentes')
def excluir_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == 'POST':
        nome_fornecedor = fornecedor.nome_fantasia
        fornecedor.delete()
        messages.success(request, f'Fornecedor "{nome_fornecedor}" excluído com sucesso!')
        return redirect('suppliers:listar_fornecedores')
    
    contexto = {
        'fornecedor': fornecedor
    }
    return render(request, 'suppliers/fornecedor_confirm_delete.html', contexto)