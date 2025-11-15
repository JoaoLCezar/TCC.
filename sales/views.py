from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from products.models import Produto, MovimentoEstoque
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import Venda, ItemVenda, SessaoCaixa
from core.decorators import group_required
from customers.models import Cliente
from .forms import SessaoCaixaForm, SessaoCaixaFechamentoForm
from django.utils import timezone
from django.contrib import messages
import json



@login_required #obrigatorio o login
@group_required('Gerentes', 'Vendedores')
def operacao_caixa(request):
    try:
        sessao_aberta = SessaoCaixa.objects.get(
            usuario=request.user, 
            status='ABERTO'
        )
    except SessaoCaixa.DoesNotExist:
        messages.error(request, 'Nenhum caixa aberto. Por favor, abra um novo caixa para iniciar as vendas.')
        return redirect('sales:abrir_caixa')
    
    produtos_disponiveis = Produto.objects.all().order_by('nome')

    clientes_cadastrados = Cliente.objects.all().order_by('nome')

    contexto = {
        'lista_de_produtos': produtos_disponiveis,
        'lista_de_clientes': clientes_cadastrados,
        'sessao_aberta': sessao_aberta,
    }

    return render(request, 'sales/caixa.html', contexto)

@login_required
@group_required('Gerentes', 'Vendedores')
@require_POST   
@transaction.atomic
def processar_venda(request):
    try:
        try:
            sessao_aberta = SessaoCaixa.objects.get(usuario=request.user, status='ABERTO')
        except SessaoCaixa.DoesNotExist:
            return JsonResponse({'sucesso': False, 'erro': 'Sessão de caixa não encontrada ou fechada.'}, status=400)
        

        data = json.loads(request.body)
        carrinho_js = data.get('carrinho')

        cliente_id = data.get('cliente_id')

        if not carrinho_js:
            return JsonResponse({'sucesso': False, 'erro': 'Carrinho vazio'}, status=400)
        
        cliente_obj = None 
        if cliente_id: 
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_id)
            except Cliente.DoesNotExist:
                return JsonResponse({'sucesso': False, 'erro': 'Cliente selecionado não foi encontrado.'}, status=404)
        
        nova_venda = Venda.objects.create(
            usuario = request.user,
            status='CONCLUIDA',
            cliente=cliente_obj,
            sessao=sessao_aberta
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

            #Registro da saida do livro de registro
            MovimentoEstoque.objects.create(
                produto=produto,
                quantidade = -quantidade_vendida,
                tipo='SAIDA_VENDA',
                usuario=request.user,
                motivo=f"Venda PDV #{nova_venda.pk}"
            )

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
@group_required('Gerentes')
def historico_vendas(request):
    filtro_status = request.GET.get('status','TODOS')
    if filtro_status == 'CONCLUIDA':
        lista_vendas = Venda.objects.filter(status='CONCLUIDA')
    elif filtro_status == 'CANCELADA':
        lista_vendas = Venda.objects.filter(status='CANCELADA')
    else:
        lista_vendas = Venda.objects.all()

    lista_vendas = lista_vendas.order_by('-data_hora')
                                         

    contexto = {
        'vendas': lista_vendas,
        'filtro_status_atual': filtro_status
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

@login_required
@group_required('Gerentes', 'Vendedores')
@require_POST
@transaction.atomic
def cancelar_venda(request):
    try:
        try:
            sessao_aberta = SessaoCaixa.objects.get(usuario=request.user, status='ABERTO')
        except SessaoCaixa.DoesNotExist:
            return JsonResponse({'sucesso': False, 'erro': 'Sessão de caixa não encontrada ou fechada.'}, status=400)
        

        data = json.loads(request.body)
        carrinho_js = data.get('carrinho')

        cliente_id = data.get('cliente_id')

        if not carrinho_js:
            return JsonResponse({'sucesso': False, 'erro': 'Carrinho vazio.'}, status=400)
        
        cliente_obj = None 
        if cliente_id:
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_id)
            except Cliente.DoesNotExist:
                return JsonResponse({'sucesso': False, 'erro': 'Cliente selecionado não foi encontrado.'}, status=404)
        
        nova_venda = Venda.objects.create(
            usuario=request.user,
            status='CANCELADA',
            cliente=cliente_obj,
            sessao=sessao_aberta
        )

        valor_total_venda = 0

        for produto_id, item_info in carrinho_js.items():
            quantidade_vendida = item_info['quantidade']


            try:
                produto = Produto.objects.get(pk=produto_id)
            except Produto.DoesNotExist:
                raise Exception(f"Produto com ID {produto_id} não encontrado.")
            
            preco_congelado = produto.preco
            subtotal_item = preco_congelado * quantidade_vendida

            ItemVenda.objects.create(
                venda=nova_venda,
                produto=produto,
                quantidade=quantidade_vendida,
                preco_unitario=preco_congelado,
                subtotal=subtotal_item
            )

            valor_total_venda += subtotal_item

        nova_venda.valor_total = valor_total_venda
        nova_venda.save()


        return JsonResponse({'sucesso': True, 'mensagem': 'Venda cancelada e registrada com sucesso!'})
    
    except json.JSONDecodeError:
        return JsonResponse({'sucesso': False, 'erro': 'Dados inválidos (JSON).'}, status=400)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)}, status=500)
    

@login_required
@group_required('Gerentes', 'Vendedores')
def abrir_caixa(request):
    sessao_existente = SessaoCaixa.objects.filter(usuario=request.user, status='ABERTO').first()
    if sessao_existente:
        messages.warning(request, 'Você já possui um caixa aberto. Redirecionado para o PDV.')
        return redirect('sales:operacao_caixa')

    if request.method == 'POST':
        form = SessaoCaixaForm(request.POST)
        if form.is_valid():
            sessao = form.save(commit=False)

            sessao.usuario = request.user
            sessao.status = 'ABERTO'

            sessao.save()

            messages.success(request, f"Caixa aberta com sucesso com R$ {sessao.valor_inicial}!")

            return redirect('sales:operacao_caixa')
        
    else:
        form = SessaoCaixaForm()

    contexto = {
        'form': form
    }

    return render(request, 'sales/abrir_caixa.html', contexto)

@login_required
@group_required('Gerentes', 'Vendedores')
def fechar_caixa(request):
    try:
        sessao_aberta = SessaoCaixa.objects.get(
            usuario=request.user,
            status='ABERTO'
        )
    except SessaoCaixa.DoesNotExist:
        # Se não tiver um caixa aberto, não há nada para fechar.
        messages.error(request, 'Você não possui um caixa aberto para fechar.')
        return redirect('dashboard') # Manda de volta para o Dashboard
    
    if request.method =='POST':
        form = SessaoCaixaFechamentoForm(request.POST)

        if form.is_valid():
            fechamento = form.save(commit=False)

            # Atualiza a sessão que encontrámos
            sessao_aberta.status = 'FECHADO'
            sessao_aberta.data_fechamento = timezone.now() # Define a hora atual
            sessao_aberta.valor_final_informado = fechamento.valor_final_informado

            sessao_aberta.save()

            # Envia uma mensagem de sucesso
            messages.success(request, f"Caixa (Sessão #{sessao_aberta.pk}) fechado com sucesso!")
            
            # Redireciona o utilizador para o Dashboard
            return redirect('dashboard')
        
    else:
        form = SessaoCaixaFechamentoForm()

    contexto = {
        'form': form,
        'sessao_aberta': sessao_aberta
    }
    
    return render(request, 'sales/fechar_caixa.html', contexto)