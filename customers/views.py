from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cliente
from .forms import ClienteForm
from core.decorators import group_required
from django.http import JsonResponse
from django.db.models import Q


# Create your views here.

@login_required
@group_required('Gerentes')
def listar_clientes(request):
    lista_de_clientes = Cliente.objects.all()

    contexto = {
        'clientes': lista_de_clientes,
    }

    return render(request, 'customers/lista_clientes.html', contexto)

@login_required
@group_required('Gerentes', 'Vendedores')
def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ClienteForm()

    context = {
        'form': form
    }

    return render(request, 'customers/form_cliente.html', context)


@login_required
@group_required('Gerentes', 'Vendedores')
def atualizar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method =='POST':
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()

            return redirect('customers:listar_clientes')
    else:
        form = ClienteForm(instance=cliente)

    contexto = {
        'form': form
    }
    return render(request, 'customers/form_cliente.html', contexto)

@login_required
@group_required('Gerentes')
def excluir_cliente(request, pk):

    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        cliente.delete()

        return redirect('customers:listar_clientes')
    
    contexto = {
        'cliente': cliente
    }
    return render(request, 'customers/cliente_confirm_delete.html', contexto)


@login_required
@group_required('Gerentes', 'Vendedores')
def api_buscar_clientes(request):
    termo = request.GET.get('term', '')

    clientes_encontrados = []

    if len(termo) >= 2:
        clientes = Cliente.objects.filter(
            Q(nome__icontains=termo) |
            Q(documento__icontains=termo)
        ).order_by('nome')[:10] # Limita 10 resultados

        clientes_encontrados = list(clientes.values('id', 'nome', 'documento'))  # Transforma a resposta do Django numa lista de dicionários

    return JsonResponse(clientes_encontrados, safe=False) # lista os dados como JSON