from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from products.models import Produto
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import Venda, ItemVenda
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
@transaction.atomic
def processar_venda(request):
    try:
        data = json.loads(request.body)
        carrinho_js = data.get('carrinho')

        if not carrinho_js:
            return JsonResponse({'sucesso': False, 'erro': 'Carrinho vazio'}, status=400)
        
        nova_venda = Venda.objects.create(
            usuario = request.user,
            status='CONCLUIDA'
        )

        valor_total_venda = 0

        for produto_id, item_info in carrinho_js.items():
            quantidade_vendida = item_info['quantidade']

            try:
                produto = Produto.objects.select_for_update().get(pk=produto_id)

            except Produto.DoesNotExist:
                    raise Exception(f"Produto com ID {produto_id} não encontrado.")
            
            if produto.estoque< quantidade_vendida:
                raise Exception(f"Estoque insuficiente para {produto.nome}.")
            
            produto.estoque -= quantidade_vendida
            produto.save()

            preco_congelado = produto.preco
            subtotal_item = preco_congelado * quantidade_vendida

            ItemVenda.objects.create(
                venda=nova_venda,
                produto=produto,
                quantidade=quantidade_vendida,
                preco_unitario=preco_congelado,
                subtotal=subtotal_item
            )


            valor_total_venda += subtotal_item #Soma o total

        nova_venda.valor_total = valor_total_venda
        nova_venda.save()



        return JsonResponse({'sucesso': True, 'mensagem': 'Venda processada com sucesso!'})
    
    except json.JSONDecodeError:
        return JsonResponse({'sucesso': False, 'erro': 'Dados inválidos (JSON).'}, status=400)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)}, status=500)
    
@login_required
def historico_vendas(request):
    lista_vendas = Venda.objects.filter(status='CONCLUIDA').order_by('-data_hora')

    contexto = {
        'vendas': lista_vendas
    }
    return render(request, 'sales/historico_vendas.html', contexto)

@login_required
def detalhe_venda(request, pk):
    venda = get_object_or_404(Venda, pk=pk)

    itens_da_venda = venda.itens.all()

    contexto = {
        'venda':venda,
        'itens_da_venda': itens_da_venda,
    }

    return render(request, 'sales/detalhe_venda.html', contexto)