from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from products.models import Produto


@login_required #obrigatorio o login
def operacao_caixa(request):
    produtos_disponiveis = Produto.objects.all().order_by('nome')

    contexto = {
        'lista_de_produtos': produtos_disponiveis,
    }

    return render(request, 'sales/caixa.html', contexto)

# Create your views here.
