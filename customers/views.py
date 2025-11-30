from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
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

    # Paginação
    try:
        per_page = int(request.GET.get('per_page', 20))
    except (TypeError, ValueError):
        per_page = 20
    if per_page not in [10, 15, 20, 25, 30, 50]:
        per_page = 20
    paginator = Paginator(lista_de_clientes, per_page)  # clientes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'clientes': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'base_querystring': f"&per_page={per_page}",
        'page_size_options': [10, 15, 20, 25, 30, 50],
    }

    return render(request, 'customers/lista_clientes.html', contexto)

@login_required
@group_required('Gerentes', 'Vendedores')
def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso!')
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
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso!')
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
        nome_cliente = cliente.nome
        cliente.delete()
        messages.success(request, f'Cliente "{nome_cliente}" excluído com sucesso!')
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