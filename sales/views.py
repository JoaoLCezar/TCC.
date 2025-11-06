from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from products.models import Produto
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


@login_required #obrigatorio o login
def operacao_caixa(request):
    produtos_disponiveis = Produto.objects.all().order_by('nome')

    contexto = {
        'lista_de_produtos': produtos_disponiveis,
    }

    return render(request, 'sales/caixa.html', contexto)

@login_required
@require_POST   
def processar_venda(request):
    try:
        data = json.loads(request.body)
        carrinho_js = data.get('carrinho')

        if not carrinho_js:
            return JsonResponse({'sucesso': False, 'erro': 'Carrinho vazio'}, status=400)

        print("="*30)
        print("Carrinho recebido com sucesso:")
        print(carrinho_js)
        print("="*30)


        return JsonResponse({'sucesso': True, 'mensagem': 'Venda processada com sucesso!'})
    
    except json.JSONDecodeError:
        return JsonResponse({'sucesso': False, 'erro': 'Dados inválidos (JSON).'}, status=400)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return JsonResponse({'sucesso': False, 'erro': str(e)}, status=500)