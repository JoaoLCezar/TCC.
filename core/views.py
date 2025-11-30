from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count
from sales.models import Venda
from products.models import Produto
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegistroUsuarioForm 
from core.decorators import group_required
import datetime


@login_required
def dashboard_view(request):
    hoje = timezone.now().date() #Obtem a data de hoje

    #Filtra as vendas de Hoje
    vendas_de_hoje = Venda.objects.filter(
        status='CONCLUIDA',
        data_hora__date=hoje
    )

    #Calcula o total
    total_vendido_hoje = vendas_de_hoje.aggregate(
        total=Sum('valor_total')
    )['total'] or 0

    total_vendas_hoje = vendas_de_hoje.count()

    total_produtos_cadastrados = Produto.objects.count()

    contexto = {
        'total_vendido_hoje': total_vendido_hoje,
        'total_vendas_hoje': total_vendas_hoje,
        'total_produtos_cadastrados': total_produtos_cadastrados,
    }

    return render(request, 'dashboard/dashboard.html', contexto)

@login_required
@group_required('Gerentes') # SÓ Gerentes podem criar novos usuários
def registrar_usuario(request):
    """
    View para cadastrar novos funcionários (Vendedores ou Gerentes).
    """
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            novo_usuario = form.save()
            messages.success(request, f"Usuário '{novo_usuario.username}' criado com sucesso!")
            return redirect('dashboard') # Ou redirecionar para uma lista de usuários
    else:
        form = RegistroUsuarioForm()
    
    contexto = {
        'form': form
    }
    return render(request, 'registration/registrar_usuario.html', contexto)