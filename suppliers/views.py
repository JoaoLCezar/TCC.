from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Fornecedor
from .forms import FornecedorForm

@login_required
def listar_fornecedores(request):
    lista_de_fornecedores = Fornecedor.objects.all()

    contexto = {
        'fornecedores': lista_de_fornecedores,
    }

    return render(request, 'suppliers/lista_fornecedores.html', contexto)


@login_required
def criar_fornecedor(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('suppliers:listar_fornecedores')
        
    else:
        form = FornecedorForm()
    
    contexto = {
        'form': form
    }

    return render(request, 'suppliers/form_fornecedor.html', contexto)

@login_required
def atualizar_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)

        if form.is_valid():
            form.save()

            return redirect('suppliers:listar_fornecedores')
        
    else:
        form = FornecedorForm(instance=fornecedor)

    contexto = {
        'form': form
    }
    return render(request, 'suppliers/form_fornecedor.html', contexto)


@login_required
def excluir_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)

    if request.method == 'POST':
        fornecedor.delete()

        return redirect('suppliers:listar_fornecedores')
    
    contexto = {
        'fornecedor': fornecedor
    }
    return render(request, 'suppliers/fornecedor_confirm_delete.html', contexto)