from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cliente
from .forms import ClienteForm

# Create your views here.

@login_required
def listar_clientes(request):
    lista_de_clientes = Cliente.objects.all()

    contexto = {
        'clientes': lista_de_clientes,
    }

    return render(request, 'customers/lista_clientes.html', contexto)

@login_required
def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('customers:listar_clientes')
    else:
        form = ClienteForm()

    context = {
        'form': form
    }

    return render(request, 'customers/form_cliente.html', context)


@login_required
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
def excluir_cliente(request, pk):

    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        cliente.delete()

        return redirect('customers:listar_clientes')
    
    contexto = {
        'cliente': cliente
    }
    return render(request, 'customers/cliente_confirm_delete.html', contexto)