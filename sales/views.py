from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from products.models import Produto, MovimentoEstoque
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction, models
from django.db.utils import OperationalError, ProgrammingError
from .models import Venda, ItemVenda, SessaoCaixa, MovimentoCaixa, Devolucao, ItemDevolucao
from core.decorators import group_required
from customers.models import Cliente
from .forms import SessaoCaixaForm, SessaoCaixaFechamentoForm
from django.utils import timezone
from decimal import Decimal
import json



@login_required #obrigatorio o login
@group_required('Gerentes', 'Vendedores')
def operacao_caixa(request):
    # Só permite acesso se o usuário tiver uma sessão de caixa aberta vinculada a si
    try:
        sessao_aberta = SessaoCaixa.objects.get(usuario=request.user, status='ABERTO')
    except SessaoCaixa.DoesNotExist:
        messages.error(request, 'Nenhum caixa aberto para este usuário. Abra seu próprio caixa para iniciar as vendas.')
        return redirect('sales:abrir_caixa')
    
    produtos_disponiveis = Produto.objects.filter(ativo=True).order_by('nome')

    clientes_cadastrados = Cliente.objects.all().order_by('nome')
    
    # Obtém categorias únicas dos produtos
    from categories.models import Categoria
    from django.db.models import Count
    
    categorias = Categoria.objects.filter(
        produto__isnull=False
    ).distinct().annotate(
        total_produtos=Count('produto')
    ).order_by('nome')

    # Cálculo de saldo do caixa da sessão atual do usuário
    from django.db.models import Sum
    vendas_sessao = Venda.objects.filter(sessao=sessao_aberta, status='CONCLUIDA')
    total_dinheiro = vendas_sessao.filter(forma_pagamento='DINHEIRO').aggregate(total=Sum('valor_total'))['total'] or 0
    total_suprimentos = MovimentoCaixa.objects.filter(sessao=sessao_aberta, tipo='SUPRIMENTO').aggregate(total=Sum('valor'))['total'] or 0
    total_sangrias = MovimentoCaixa.objects.filter(sessao=sessao_aberta, tipo='SANGRIA').aggregate(total=Sum('valor'))['total'] or 0
    saldo_atual = (sessao_aberta.valor_inicial or 0) + total_dinheiro + total_suprimentos - total_sangrias

    # Se gerente, permitir escolher uma sessão alvo para movimento
    is_gerente = request.user.groups.filter(name='Gerentes').exists()
    sessoes_abertas = None
    if is_gerente:
        sessoes_abertas = SessaoCaixa.objects.filter(status='ABERTO').select_related('usuario').order_by('-data_abertura')[:50]

    contexto = {
        'lista_de_produtos': produtos_disponiveis,
        'lista_de_clientes': clientes_cadastrados,
        'sessao_aberta': sessao_aberta,
        'categorias': categorias,
        'saldo_valor_inicial': sessao_aberta.valor_inicial,
        'saldo_total_dinheiro': total_dinheiro,
        'saldo_total_suprimentos': total_suprimentos,
        'saldo_total_sangrias': total_sangrias,
        'saldo_atual': saldo_atual,
        'sessoes_abertas': sessoes_abertas,
        'is_gerente': is_gerente,
    }

    return render(request, 'sales/caixa.html', contexto)


@login_required
@group_required('Gerentes')
@transaction.atomic
def registrar_movimento_caixa(request):
    if request.method != 'POST':
        return redirect('sales:operacao_caixa')

    # Determina a sessão alvo: por padrão a do usuário; se gerente e for passado sessao_id, usa a informada (se aberta)
    sessao_aberta = None
    sessao_id_post = request.POST.get('sessao_id')
    if sessao_id_post and request.user.groups.filter(name='Gerentes').exists():
        try:
            sessao_aberta = SessaoCaixa.objects.get(pk=sessao_id_post, status='ABERTO')
        except SessaoCaixa.DoesNotExist:
            sessao_aberta = None
    if not sessao_aberta:
        try:
            sessao_aberta = SessaoCaixa.objects.get(usuario=request.user, status='ABERTO')
        except SessaoCaixa.DoesNotExist:
            messages.error(request, 'Nenhum caixa aberto para registrar o movimento.')
            return redirect('sales:abrir_caixa')

    tipo = request.POST.get('tipo')
    valor_str = request.POST.get('valor')
    motivo = (request.POST.get('motivo') or '').strip()

    if tipo not in ['SUPRIMENTO', 'SANGRIA']:
        messages.error(request, 'Tipo de movimento inválido.')
        return redirect('sales:operacao_caixa')

    # Motivo obrigatório para SANGRIA
    if tipo == 'SANGRIA' and not motivo:
        messages.error(request, 'Informe o motivo para a sangria.')
        return redirect('sales:operacao_caixa')

    try:
        valor = float(valor_str)
    except (TypeError, ValueError):
        messages.error(request, 'Valor inválido.')
        return redirect('sales:operacao_caixa')

    if valor <= 0:
        messages.error(request, 'O valor deve ser maior que zero.')
        return redirect('sales:operacao_caixa')

    MovimentoCaixa.objects.create(
        sessao=sessao_aberta,
        usuario=request.user,
        tipo=tipo,
        valor=valor,
        motivo=motivo,
    )
    messages.success(request, f"{ 'Suprimento' if tipo=='SUPRIMENTO' else 'Sangria' } registrado com sucesso!")
    return redirect('sales:operacao_caixa')


@login_required
@group_required('Gerentes')
@require_POST
@transaction.atomic
def cancelar_venda_existente(request, venda_id: int):
    venda = get_object_or_404(Venda, pk=venda_id)
    if venda.status != 'CONCLUIDA':
        messages.warning(request, 'Apenas vendas concluídas podem ser canceladas.')
        return redirect('sales:detalhe_venda', pk=venda.pk)

    motivo_cancel = (request.POST.get('motivo') or '').strip()
    if not motivo_cancel:
        messages.error(request, 'Informe o motivo do cancelamento.')
        return redirect('sales:detalhe_venda', pk=venda.pk)

    # Repor estoque e registrar movimento de estoque
    itens = venda.itens.select_related('produto').all()
    for item in itens:
        produto = Produto.objects.select_for_update().get(pk=item.produto.pk)
        produto.estoque += item.quantidade
        produto.save()
        MovimentoEstoque.objects.create(
            produto=produto,
            quantidade=item.quantidade,
            tipo='ENTRADA',
            usuario=request.user,
            motivo=f'Cancelamento da venda #{venda.pk}'
        )

    venda.status = 'CANCELADA'
    venda.save()

    # Registrar sangria automática se a venda foi paga em dinheiro
    try:
        if venda.forma_pagamento == 'DINHEIRO' and venda.valor_total and venda.valor_total > 0:
            sessao_mov = None
            try:
                sessao_mov = SessaoCaixa.objects.get(usuario=request.user, status='ABERTO')
            except SessaoCaixa.DoesNotExist:
                if venda.sessao and venda.sessao.status == 'ABERTO':
                    sessao_mov = venda.sessao
            if sessao_mov:
                MovimentoCaixa.objects.create(
                    sessao=sessao_mov,
                    usuario=request.user,
                    tipo='SANGRIA',
                    valor=venda.valor_total,
                    motivo=f'Reembolso por cancelamento da venda #{venda.pk}: {motivo_cancel}'[:255]
                )
            else:
                messages.warning(request, 'Cancelamento registrado, mas não foi possível registrar a sangria (nenhum caixa aberto).')
    except Exception:
        messages.warning(request, 'Cancelamento realizado, porém ocorreu um problema ao registrar a sangria.')

    messages.success(request, f'Venda #{venda.pk} cancelada e itens retornados ao estoque.')
    return redirect('sales:historico_vendas')

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
        forma_pagamento = data.get('forma_pagamento', 'DINHEIRO')
        desconto_tipo = data.get('desconto_tipo')  # 'valor' ou 'percentual'
        try:
            desconto_input = Decimal(str(data.get('desconto_input') or '0'))
        except Exception:
            desconto_input = Decimal('0')

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
            sessao=sessao_aberta,
            forma_pagamento=forma_pagamento
        )

        valor_total_venda = 0

        for produto_id, item_info in carrinho_js.items():
            quantidade_vendida = item_info['quantidade']

            try:
                produto = Produto.objects.select_for_update().get(pk=produto_id)

            except Produto.DoesNotExist:
                    raise Exception(f"Produto com ID {produto_id} não encontrado.")
            
            if produto.estoque< quantidade_vendida:
                raise Exception(f"Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}, Solicitado: {quantidade_vendida}")
            
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

        # calcula desconto
        desconto_total = Decimal('0')
        if desconto_tipo == 'percentual':
            if desconto_input < 0:
                desconto_input = Decimal('0')
            if desconto_input > 100:
                desconto_input = Decimal('100')
            desconto_total = (valor_total_venda * desconto_input) / Decimal('100')
        elif desconto_tipo == 'valor':
            if desconto_input < 0:
                desconto_input = Decimal('0')
            if desconto_input > valor_total_venda:
                desconto_input = Decimal(valor_total_venda)
            desconto_total = desconto_input

        nova_venda.valor_total = valor_total_venda - desconto_total
        nova_venda.save()

        return JsonResponse({'sucesso': True, 'mensagem': 'Venda processada com sucesso!', 'venda_id': nova_venda.pk})
    
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
    
    # Paginação
    try:
        per_page = int(request.GET.get('per_page', 30))
    except (TypeError, ValueError):
        per_page = 30
    if per_page not in [10, 15, 20, 25, 30, 50]:
        per_page = 30
    paginator = Paginator(lista_vendas, per_page)  # vendas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'vendas': page_obj,
        'filtro_status_atual': filtro_status,
        'page_obj': page_obj,
        'per_page': per_page,
        'base_querystring': f"&status={filtro_status}&per_page={per_page}",
        'page_size_options': [10, 15, 20, 25, 30, 50],
    }
    return render(request, 'sales/historico_vendas.html', contexto)

@login_required
@group_required('Gerentes')
def detalhe_venda(request, pk):
    venda = get_object_or_404(Venda, pk=pk)

    itens_da_venda = venda.itens.all()
    # calcular já devolvido por item e acoplar no objeto
    for item in itens_da_venda:
        try:
            qtd_dev = ItemDevolucao.objects.filter(item_venda=item).aggregate(total=models.Sum('quantidade'))['total'] or 0
        except (OperationalError, ProgrammingError):
            qtd_dev = 0
        setattr(item, 'qtd_devolvida', qtd_dev)

    contexto = {
        'venda':venda,
        'itens_da_venda': itens_da_venda,
    }

    return render(request, 'sales/detalhe_venda.html', contexto)


@login_required
@group_required('Gerentes', 'Vendedores')
def imprimir_recibo(request, venda_id: int):
    venda = get_object_or_404(Venda, pk=venda_id)
    itens = venda.itens.all()
    # calcula subtotal dos itens e desconto inferido (se houver)
    subtotal_itens = sum((item.subtotal for item in itens), 0)
    try:
        # Garantir tipos numéricos simples para cálculo
        subtotal_float = float(subtotal_itens)
        total_float = float(venda.valor_total)
    except Exception:
        subtotal_float = 0.0
        total_float = 0.0
    desconto_inferido = max(0.0, round(subtotal_float - total_float, 2))

    contexto = {
        'venda': venda,
        'itens': itens,
        'subtotal_itens': subtotal_float,
        'desconto_inferido': desconto_inferido,
    }
    return render(request, 'sales/recibo.html', contexto)


@login_required
@group_required('Gerentes', 'Vendedores')
@transaction.atomic
def registrar_devolucao(request, venda_id: int):
    venda = get_object_or_404(Venda, pk=venda_id)

    try:
        sessao_aberta = SessaoCaixa.objects.get(usuario=request.user, status='ABERTO')
    except SessaoCaixa.DoesNotExist:
        messages.error(request, 'Abra um caixa para registrar devoluções.')
        return redirect('sales:abrir_caixa')

    if request.method == 'GET':
        itens = venda.itens.all()
        for item in itens:
            try:
                qtd_dev = ItemDevolucao.objects.filter(item_venda=item).aggregate(total=models.Sum('quantidade'))['total'] or 0
            except (OperationalError, ProgrammingError):
                qtd_dev = 0
            setattr(item, 'qtd_devolvida', qtd_dev)
        return render(request, 'sales/registrar_devolucao.html', {
            'venda': venda,
            'itens': itens,
        })

    # POST
    itens = venda.itens.all()
    total_devolucao = 0
    devolucao = Devolucao.objects.create(
        venda=venda,
        sessao=sessao_aberta,
        usuario=request.user,
        motivo=request.POST.get('motivo') or ''
    )

    algo_devolvido = False
    for item in itens:
        qtd_str = request.POST.get(f'qtd_{item.id}', '0').strip()
        try:
            qtd_dev = int(qtd_str or '0')
        except ValueError:
            qtd_dev = 0
        if qtd_dev <= 0:
            continue
        # validar limite: vendidos - já devolvidos
        qtd_ja_dev = ItemDevolucao.objects.filter(item_venda=item).aggregate(total=models.Sum('quantidade'))['total'] or 0
        max_pode = max(0, item.quantidade - qtd_ja_dev)
        if qtd_dev > max_pode:
            qtd_dev = max_pode
        if qtd_dev <= 0:
            continue

        subtotal = float(item.preco_unitario) * qtd_dev
        ItemDevolucao.objects.create(
            devolucao=devolucao,
            produto=item.produto,
            item_venda=item,
            quantidade=qtd_dev,
            valor_unitario=item.preco_unitario,
            subtotal=subtotal
        )
        # repõe estoque
        item.produto.estoque += qtd_dev
        item.produto.save()
        MovimentoEstoque.objects.create(
            produto=item.produto,
            quantidade=qtd_dev,
            tipo='ENTRADA',
            usuario=request.user,
            motivo=f'Devolução da venda #{venda.pk}'
        )
        total_devolucao += subtotal
        algo_devolvido = True

    if not algo_devolvido:
        devolucao.delete()
        messages.warning(request, 'Nenhuma quantidade válida informada para devolução.')
        return redirect('sales:detalhe_venda', pk=venda.pk)

    devolucao.valor_total = total_devolucao
    devolucao.save()

    # se a venda original foi DINHEIRO, registra saída (sangria) do valor reembolsado
    if venda.forma_pagamento == 'DINHEIRO' and total_devolucao > 0:
        MovimentoCaixa.objects.create(
            sessao=sessao_aberta,
            usuario=request.user,
            tipo='SANGRIA',
            valor=total_devolucao,
            motivo=f'Reembolso devolução da venda #{venda.pk}'
        )

    messages.success(request, f'Devolução registrada. Total reembolsado: R$ {total_devolucao:.2f}')
    return redirect('sales:detalhe_venda', pk=venda.pk)

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