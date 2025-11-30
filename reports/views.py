from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, F, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from core.decorators import group_required
from sales.models import Venda, ItemVenda, SessaoCaixa, MovimentoCaixa
from products.models import Produto, MovimentoEstoque
from customers.models import Cliente
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.contrib.auth.models import User


@login_required
@group_required('Gerentes')
def menu_relatorios(request):
    """Menu principal de relatórios"""
    return render(request, 'reports/menu_relatorios.html')


@login_required
@group_required('Gerentes')
def relatorio_caixa(request):
    """Relatório do Caixa: totais por período ou por sessão e por forma de pagamento"""
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    sessao_id = request.GET.get('sessao_id')
    usuario_id = request.GET.get('usuario_id')

    vendas = Venda.objects.all()

    if sessao_id:
        vendas = vendas.filter(sessao_id=sessao_id)
    else:
        # Padrão: últimos 7 dias
        if data_inicio:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            data_inicio_obj = timezone.now() - timedelta(days=7)
            data_inicio = data_inicio_obj.strftime('%Y-%m-%d')
        if data_fim:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        else:
            data_fim_obj = timezone.now()
            data_fim = data_fim_obj.strftime('%Y-%m-%d')
        vendas = vendas.filter(data_hora__gte=data_inicio_obj, data_hora__lt=data_fim_obj)

    vendas_concluidas = vendas.filter(status='CONCLUIDA')
    if usuario_id:
        vendas_concluidas = vendas_concluidas.filter(usuario_id=usuario_id)
    vendas_canceladas = vendas.filter(status='CANCELADA')

    total_recebido = vendas_concluidas.aggregate(total=Sum('valor_total'))['total'] or 0
    qtd_concluidas = vendas_concluidas.count()
    qtd_canceladas = vendas_canceladas.count()
    ticket_medio = (total_recebido / qtd_concluidas) if qtd_concluidas else 0

    # Totais por forma de pagamento
    por_forma = list(
        vendas_concluidas.values('forma_pagamento')
        .annotate(total=Sum('valor_total'), quantidade=Count('id'))
        .order_by('forma_pagamento')
    )

    # Totais por vendedor
    por_vendedor = list(
        vendas_concluidas.values('usuario__username')
        .annotate(total=Sum('valor_total'), quantidade=Count('id'))
        .order_by('-total')
    )
    # adicionar percentual de participação
    por_vendedor = [
        {
            **row,
            'percentual': float((row['total'] / total_recebido) * 100) if total_recebido else 0.0
        }
        for row in por_vendedor
    ]

    # Totais por sessão
    por_sessao = list(
        vendas_concluidas.values('sessao__id', 'sessao__usuario__username', 'sessao__data_abertura', 'sessao__status')
        .annotate(total=Sum('valor_total'), quantidade=Count('id'))
        .order_by('-sessao__data_abertura')[:50]
    )

    # Opções de sessões para filtro
    sessoes = SessaoCaixa.objects.order_by('-data_abertura')[:100]
    vendedores = User.objects.filter(vendas__status='CONCLUIDA').distinct().order_by('username')

    # Resumo da sessão selecionada (se houver)
    sessao_escolhida = None
    esperado_final = None
    diferenca = None
    total_dinheiro = None
    total_suprimentos = None
    total_sangrias = None
    if sessao_id:
        try:
            sessao_escolhida = SessaoCaixa.objects.get(pk=sessao_id)
            # Considera fechamento de caixa em DINHEIRO + movimentos de caixa
            total_dinheiro = vendas_concluidas.filter(forma_pagamento='DINHEIRO').aggregate(total=Sum('valor_total'))['total'] or 0
            total_suprimentos = MovimentoCaixa.objects.filter(sessao_id=sessao_id, tipo='SUPRIMENTO').aggregate(total=Sum('valor'))['total'] or 0
            total_sangrias = MovimentoCaixa.objects.filter(sessao_id=sessao_id, tipo='SANGRIA').aggregate(total=Sum('valor'))['total'] or 0
            esperado_final = (sessao_escolhida.valor_inicial or 0) + total_dinheiro + total_suprimentos - total_sangrias
            if sessao_escolhida.valor_final_informado is not None:
                diferenca = sessao_escolhida.valor_final_informado - esperado_final
        except SessaoCaixa.DoesNotExist:
            sessao_escolhida = None

    contexto = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'sessao_id': int(sessao_id) if sessao_id else None,
        'sessoes': sessoes,
        'vendedores': vendedores,
        'usuario_id': int(usuario_id) if usuario_id else None,
        'total_recebido': total_recebido,
        'qtd_concluidas': qtd_concluidas,
        'qtd_canceladas': qtd_canceladas,
        'ticket_medio': ticket_medio,
        'por_forma': por_forma,
        'por_vendedor': por_vendedor,
        'por_sessao': por_sessao,
        'sessao_escolhida': sessao_escolhida,
        'esperado_final': esperado_final,
        'diferenca': diferenca,
        'total_dinheiro': total_dinheiro,
        'total_suprimentos': total_suprimentos,
        'total_sangrias': total_sangrias,
    }

    return render(request, 'reports/relatorio_caixa.html', contexto)


@login_required
@group_required('Gerentes')
def relatorio_caixa_pdf(request):
    """PDF do Relatório do Caixa (resumo)"""
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    sessao_id = request.GET.get('sessao_id')

    vendas = Venda.objects.all()
    if sessao_id:
        vendas = vendas.filter(sessao_id=sessao_id)
        periodo_str = f"Sessão #{sessao_id}"
    else:
        if data_inicio:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            data_inicio_obj = timezone.now() - timedelta(days=7)
            data_inicio = data_inicio_obj.strftime('%Y-%m-%d')
        if data_fim:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        else:
            data_fim_obj = timezone.now()
            data_fim = data_fim_obj.strftime('%Y-%m-%d')
        vendas = vendas.filter(data_hora__gte=data_inicio_obj, data_hora__lt=data_fim_obj)
        periodo_str = f"{data_inicio} a {data_fim}"

    vendas_concluidas = vendas.filter(status='CONCLUIDA')

    total_recebido = vendas_concluidas.aggregate(total=Sum('valor_total'))['total'] or 0
    qtd_concluidas = vendas_concluidas.count()
    ticket_medio = (total_recebido / qtd_concluidas) if qtd_concluidas else 0

    por_forma = list(
        vendas_concluidas.values('forma_pagamento')
        .annotate(total=Sum('valor_total'), quantidade=Count('id'))
        .order_by('forma_pagamento')
    )

    por_vendedor = list(
        vendas_concluidas.values('usuario__username')
        .annotate(total=Sum('valor_total'), quantidade=Count('id'))
        .order_by('-total')
    )
    por_vendedor = [
        {
            **row,
            'percentual': float((row['total'] / total_recebido) * 100) if total_recebido else 0.0
        }
        for row in por_vendedor
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], fontSize=24,
        textColor=colors.HexColor('#0d6efd'), spaceAfter=30, alignment=TA_CENTER
    )

    elements.append(Paragraph('VendaFácil PDV', title_style))
    elements.append(Paragraph('Relatório do Caixa', styles['Heading2']))
    elements.append(Paragraph(f'Período: {periodo_str}', styles['Normal']))
    elements.append(Spacer(1, 20))

    stats_data = [
        ['Total Recebido:', f'R$ {total_recebido:,.2f}'],
        ['Vendas Concluídas:', f'{qtd_concluidas}'],
        ['Ticket Médio:', f'R$ {ticket_medio:,.2f}'],
    ]
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # Por forma de pagamento
    fp_data = [['Forma de Pagamento', 'Qtd', 'Total']]
    for row in por_forma:
        fp_data.append([
            row['forma_pagamento'], str(row['quantidade']), f"R$ {row['total']:,.2f}"
        ])
    fp_table = Table(fp_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
    fp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(fp_table)

    elements.append(Spacer(1, 16))
    # Por vendedor
    vend_data = [['Vendedor', 'Qtd', 'Total', '%']]
    for row in por_vendedor:
        vend_data.append([
            (row['usuario__username'] or 'Não atribuído'), str(row['quantidade']), f"R$ {row['total']:,.2f}", f"{row['percentual']:.1f}%"
        ])
    vend_table = Table(vend_data, colWidths=[2.2*inch, 0.8*inch, 1.3*inch, 0.7*inch])
    vend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(vend_table)

    # Se for por sessão, incluir resumo financeiro
    if sessao_id:
        try:
            sessao = SessaoCaixa.objects.get(pk=sessao_id)
            total_dinheiro = vendas_concluidas.filter(forma_pagamento='DINHEIRO').aggregate(total=Sum('valor_total'))['total'] or 0
            total_suprimentos = MovimentoCaixa.objects.filter(sessao_id=sessao_id, tipo='SUPRIMENTO').aggregate(total=Sum('valor'))['total'] or 0
            total_sangrias = MovimentoCaixa.objects.filter(sessao_id=sessao_id, tipo='SANGRIA').aggregate(total=Sum('valor'))['total'] or 0
            esperado_final = (sessao.valor_inicial or 0) + total_dinheiro + total_suprimentos - total_sangrias
            diff = None
            if sessao.valor_final_informado is not None:
                diff = sessao.valor_final_informado - esperado_final
            elements.append(Spacer(1, 16))
            resumo_data = [
                ['Abertura (Suprimento):', f"R$ {sessao.valor_inicial:,.2f}"],
                ['Recebido em Dinheiro:', f"R$ {total_dinheiro:,.2f}"],
                ['Suprimentos:', f"R$ {total_suprimentos:,.2f}"],
                ['Sangrias:', f"R$ {total_sangrias:,.2f}"],
            ]
            if sessao.valor_final_informado is not None:
                resumo_data.append(['Fechamento (Informado):', f"R$ {sessao.valor_final_informado:,.2f}"])
                resumo_data.append(['Esperado:', f"R$ {esperado_final:,.2f}"])
                resumo_data.append(['Diferença (Inf - Esp):', f"R$ {diff:,.2f}"])
            resumo_table = Table(resumo_data, colWidths=[3*inch, 2*inch])
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            elements.append(resumo_table)
        except SessaoCaixa.DoesNotExist:
            pass

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f"attachment; filename=relatorio_caixa_{timezone.now().strftime('%Y%m%d')}.pdf"
    return response


@login_required
@group_required('Gerentes')
def relatorio_vendas(request):
    """Relatório de vendas com filtros de data"""
    # Pegar filtros da URL
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Filtro base
    vendas = Venda.objects.filter(status='CONCLUIDA')
    
    # Aplicar filtros de data
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
    else:
        # Por padrão, últimos 30 dias
        data_inicio_obj = timezone.now() - timedelta(days=30)
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%Y-%m-%d')
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        # Adicionar 1 dia para incluir o dia inteiro
        data_fim_obj = data_fim_obj + timedelta(days=1)
        vendas = vendas.filter(data_hora__lt=data_fim_obj)
    else:
        data_fim = timezone.now().strftime('%Y-%m-%d')
    
    # Calcular estatísticas
    total_vendas = vendas.count()
    valor_total = vendas.aggregate(total=Sum('valor_total'))['total'] or 0
    ticket_medio = vendas.aggregate(media=Avg('valor_total'))['media'] or 0
    
    # Vendas por dia
    vendas_por_dia = vendas.extra(
        select={'dia': 'DATE(data_hora)'}
    ).values('dia').annotate(
        total=Sum('valor_total'),
        quantidade=Count('id')
    ).order_by('-dia')
    
    # Produtos mais vendidos
    produtos_vendidos = ItemVenda.objects.filter(
        venda__in=vendas
    ).values(
        'produto__nome'
    ).annotate(
        quantidade_total=Sum('quantidade'),
        valor_total=Sum('subtotal')
    ).order_by('-quantidade_total')[:10]
    
    contexto = {
        'vendas': vendas.order_by('-data_hora')[:50],
        'total_vendas': total_vendas,
        'valor_total': valor_total,
        'ticket_medio': ticket_medio,
        'vendas_por_dia': vendas_por_dia,
        'produtos_vendidos': produtos_vendidos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'reports/relatorio_vendas.html', contexto)


@login_required
@group_required('Gerentes')
def relatorio_vendas_pdf(request):
    """Gerar PDF do relatório de vendas"""
    # Pegar os mesmos filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    vendas = Venda.objects.filter(status='CONCLUIDA')
    
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
    else:
        data_inicio_obj = timezone.now() - timedelta(days=30)
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim_obj = data_fim_obj + timedelta(days=1)
        vendas = vendas.filter(data_hora__lt=data_fim_obj)
        data_fim = data_fim_obj.strftime('%d/%m/%Y')
    else:
        data_fim = timezone.now().strftime('%d/%m/%Y')
    
    # Criar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph('VendaFácil PDV', title_style))
    elements.append(Paragraph(f'Relatório de Vendas', styles['Heading2']))
    elements.append(Paragraph(f'Período: {data_inicio} a {data_fim}', styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Estatísticas
    total_vendas = vendas.count()
    valor_total = vendas.aggregate(total=Sum('valor_total'))['total'] or 0
    
    stats_data = [
        ['Total de Vendas:', f'{total_vendas}'],
        ['Valor Total:', f'R$ {valor_total:,.2f}'],
        ['Ticket Médio:', f'R$ {(valor_total/total_vendas if total_vendas > 0 else 0):,.2f}'],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 30))
    
    # Tabela de vendas
    elements.append(Paragraph('Detalhamento das Vendas', styles['Heading3']))
    elements.append(Spacer(1, 10))
    
    vendas_data = [['Data/Hora', 'Cliente', 'Valor', 'Usuário']]
    for venda in vendas.order_by('-data_hora')[:50]:
        vendas_data.append([
            venda.data_hora.strftime('%d/%m/%Y %H:%M'),
            venda.cliente.nome if venda.cliente else 'N/A',
            f'R$ {venda.valor_total:,.2f}',
            venda.usuario.username
        ])
    
    vendas_table = Table(vendas_data, colWidths=[1.5*inch, 2*inch, 1.2*inch, 1.3*inch])
    vendas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(vendas_table)
    
    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_vendas_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
@group_required('Gerentes')
def relatorio_produtos(request):
    """Relatório de produtos"""
    produtos = Produto.objects.all().annotate(
        valor_estoque=F('preco') * F('estoque')
    ).order_by('nome')
    
    # Estatísticas
    total_produtos = produtos.count()
    valor_total_estoque = produtos.aggregate(total=Sum('valor_estoque'))['total'] or 0
    produtos_zerados = produtos.filter(estoque=0).count()
    produtos_baixo_estoque = produtos.filter(estoque__lte=10, estoque__gt=0).count()
    
    contexto = {
        'produtos': produtos,
        'total_produtos': total_produtos,
        'valor_total_estoque': valor_total_estoque,
        'produtos_zerados': produtos_zerados,
        'produtos_baixo_estoque': produtos_baixo_estoque,
    }
    
    return render(request, 'reports/relatorio_produtos.html', contexto)


@login_required
@group_required('Gerentes')
def relatorio_produtos_pdf(request):
    """Gerar PDF do relatório de produtos"""
    produtos = Produto.objects.all().annotate(
        valor_estoque=F('preco') * F('estoque')
    ).order_by('nome')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph('VendaFácil PDV', title_style))
    elements.append(Paragraph('Relatório de Produtos', styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Tabela de produtos
    produtos_data = [['Produto', 'Categoria', 'Preço', 'Estoque', 'Valor Total']]
    for produto in produtos:
        produtos_data.append([
            produto.nome,
            produto.categoria.nome if produto.categoria else 'N/A',
            f'R$ {produto.preco:,.2f}',
            str(produto.estoque),
            f'R$ {produto.valor_estoque:,.2f}'
        ])
    
    produtos_table = Table(produtos_data, colWidths=[2*inch, 1.5*inch, 1*inch, 0.8*inch, 1.2*inch])
    produtos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(produtos_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_produtos_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
@group_required('Gerentes')
def relatorio_estoque(request):
    """Relatório de movimentação de estoque"""
    # Pegar filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    movimentos = MovimentoEstoque.objects.all()
    
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        movimentos = movimentos.filter(data_hora__gte=data_inicio_obj)
    else:
        data_inicio_obj = timezone.now() - timedelta(days=30)
        movimentos = movimentos.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%Y-%m-%d')
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim_obj = data_fim_obj + timedelta(days=1)
        movimentos = movimentos.filter(data_hora__lt=data_fim_obj)
    else:
        data_fim = timezone.now().strftime('%Y-%m-%d')
    
    movimentos = movimentos.order_by('-data_hora')[:100]
    
    # Estatísticas
    total_entradas = MovimentoEstoque.objects.filter(
        tipo='ENTRADA',
        data_hora__gte=data_inicio
    ).aggregate(total=Sum('quantidade'))['total'] or 0
    
    total_saidas = abs(MovimentoEstoque.objects.filter(
        tipo='SAIDA_VENDA',
        data_hora__gte=data_inicio
    ).aggregate(total=Sum('quantidade'))['total'] or 0)
    
    contexto = {
        'movimentos': movimentos,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'reports/relatorio_estoque.html', contexto)


@login_required
@group_required('Gerentes')
def relatorio_estoque_pdf(request):
    """Gerar PDF do relatório de estoque"""
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    movimentos = MovimentoEstoque.objects.all()
    
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        movimentos = movimentos.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
    else:
        data_inicio_obj = timezone.now() - timedelta(days=30)
        movimentos = movimentos.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim_obj = data_fim_obj + timedelta(days=1)
        movimentos = movimentos.filter(data_hora__lt=data_fim_obj)
        data_fim = data_fim_obj.strftime('%d/%m/%Y')
    else:
        data_fim = timezone.now().strftime('%d/%m/%Y')
    
    movimentos = movimentos.order_by('-data_hora')[:100]
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph('VendaFácil PDV', title_style))
    elements.append(Paragraph('Relatório de Movimentação de Estoque', styles['Heading2']))
    elements.append(Paragraph(f'Período: {data_inicio} a {data_fim}', styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Tabela de movimentos
    movimentos_data = [['Data', 'Produto', 'Tipo', 'Quantidade', 'Usuário']]
    for movimento in movimentos:
        tipo = 'Entrada' if movimento.tipo == 'ENTRADA' else 'Saída'
        movimentos_data.append([
            movimento.data_hora.strftime('%d/%m/%Y %H:%M'),
            movimento.produto.nome,
            tipo,
            str(movimento.quantidade),
            movimento.usuario.username
        ])
    
    movimentos_table = Table(movimentos_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 1*inch])
    movimentos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(movimentos_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_estoque_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
@group_required('Gerentes')
def relatorio_clientes(request):
    """Relatório de clientes"""
    # Query base com anotações
    clientes_qs = Cliente.objects.all().annotate(
        total_compras=Count('vendas', filter=Q(vendas__status='CONCLUIDA')),
        valor_total=Sum('vendas__valor_total', filter=Q(vendas__status='CONCLUIDA'))
    ).order_by('-valor_total')

    # Estatísticas antes da paginação
    total_clientes = clientes_qs.count()
    clientes_ativos = clientes_qs.filter(total_compras__gt=0).count()

    # Paginação
    try:
        per_page = int(request.GET.get('per_page', 25))
    except (TypeError, ValueError):
        per_page = 25
    if per_page not in [10, 15, 20, 25, 30, 50]:
        per_page = 25
    page_number = request.GET.get('page')
    paginator = Paginator(clientes_qs, per_page)
    page_obj = paginator.get_page(page_number)

    contexto = {
        'clientes': page_obj,
        'page_obj': page_obj,
        'total_clientes': total_clientes,
        'clientes_ativos': clientes_ativos,
        'per_page': per_page,
        'base_querystring': f"&per_page={per_page}",
        'page_size_options': [10, 15, 20, 25, 30, 50],
    }

    return render(request, 'reports/relatorio_clientes.html', contexto)


@login_required
@group_required('Gerentes')
def relatorio_clientes_pdf(request):
    """Gerar PDF do relatório de clientes"""
    from django.db import models
    
    clientes = Cliente.objects.all().annotate(
        total_compras=Count('vendas', filter=models.Q(vendas__status='CONCLUIDA')),
        valor_total=Sum('vendas__valor_total', filter=models.Q(vendas__status='CONCLUIDA'))
    ).order_by('-valor_total')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph('VendaFácil PDV', title_style))
    elements.append(Paragraph('Relatório de Clientes', styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Tabela de clientes
    clientes_data = [['Cliente', 'Documento', 'Total Compras', 'Valor Total']]
    for cliente in clientes:
        clientes_data.append([
            cliente.nome,
            cliente.documento or 'N/A',
            str(cliente.total_compras or 0),
            f'R$ {(cliente.valor_total or 0):,.2f}'
        ])
    
    clientes_table = Table(clientes_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1.3*inch])
    clientes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(clientes_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_clientes_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
@group_required('Gerentes')
def relatorio_lucratividade(request):
    """Relatório de lucratividade por produto"""
    # Pegar filtros da URL
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Filtro base - apenas vendas concluídas
    vendas = Venda.objects.filter(status='CONCLUIDA')
    
    # Aplicar filtros de data
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
    else:
        # Por padrão, últimos 30 dias
        data_inicio_obj = timezone.now() - timedelta(days=30)
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%Y-%m-%d')
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim_obj = data_fim_obj + timedelta(days=1)
        vendas = vendas.filter(data_hora__lt=data_fim_obj)
    else:
        data_fim = timezone.now().strftime('%Y-%m-%d')
    
    # Buscar itens vendidos e calcular lucro
    itens_vendidos_raw = ItemVenda.objects.filter(
        venda__in=vendas
    ).select_related('produto', 'venda').order_by('-venda__data_hora')[:100]
    
    # Adicionar cálculos de lucro a cada item
    itens_vendidos = []
    for item in itens_vendidos_raw:
        custo_total = (item.produto.preco_custo or 0) * item.quantidade
        lucro = item.subtotal - custo_total
        margem = (lucro * 100 / item.subtotal) if item.subtotal > 0 else 0
        
        item.custo_total = custo_total
        item.lucro = lucro
        item.margem_lucro = margem
        itens_vendidos.append(item)
    
    # Agrupar por produto para resumo
    from django.db import models
    resumo_produtos = ItemVenda.objects.filter(
        venda__in=vendas
    ).values(
        'produto__nome', 'produto__preco_custo'
    ).annotate(
        quantidade_vendida=Sum('quantidade'),
        receita_total=Sum('subtotal'),
    ).order_by('-receita_total')
    
    # Calcular lucro e margem para cada produto
    resumo_list = []
    receita_total = 0
    custo_total = 0
    lucro_total = 0
    
    for item in resumo_produtos:
        custo = (item['produto__preco_custo'] or 0) * item['quantidade_vendida']
        lucro = item['receita_total'] - custo
        margem = (lucro * 100 / item['receita_total']) if item['receita_total'] > 0 else 0
        
        resumo_list.append({
            'produto__nome': item['produto__nome'],
            'quantidade_vendida': item['quantidade_vendida'],
            'receita_total': item['receita_total'],
            'custo_total': custo,
            'lucro_total': lucro,
            'margem_lucro': margem
        })
        
        receita_total += item['receita_total']
        custo_total += custo
        lucro_total += lucro
    
    # Ordenar por lucro
    resumo_list.sort(key=lambda x: x['lucro_total'], reverse=True)
    
    margem_lucro_geral = (lucro_total * 100 / receita_total) if receita_total > 0 else 0
    
    contexto = {
        'itens_vendidos': itens_vendidos,
        'resumo_produtos': resumo_list,
        'receita_total': receita_total,
        'custo_total': custo_total,
        'lucro_total': lucro_total,
        'margem_lucro_geral': margem_lucro_geral,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'reports/relatorio_lucratividade.html', contexto)


@login_required
@group_required('Gerentes')
def relatorio_lucratividade_pdf(request):
    """Gerar PDF do relatório de lucratividade"""
    # Pegar os mesmos filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    vendas = Venda.objects.filter(status='CONCLUIDA')
    
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
    else:
        data_inicio_obj = timezone.now() - timedelta(days=30)
        vendas = vendas.filter(data_hora__gte=data_inicio_obj)
        data_inicio = data_inicio_obj.strftime('%d/%m/%Y')
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim_obj = data_fim_obj + timedelta(days=1)
        vendas = vendas.filter(data_hora__lt=data_fim_obj)
        data_fim = data_fim_obj.strftime('%d/%m/%Y')
    else:
        data_fim = timezone.now().strftime('%d/%m/%Y')
    
    # Resumo por produto
    from django.db import models
    resumo_produtos = ItemVenda.objects.filter(
        venda__in=vendas
    ).values(
        'produto__nome', 'produto__preco_custo'
    ).annotate(
        quantidade_vendida=Sum('quantidade'),
        receita_total=Sum('subtotal'),
    ).order_by('-receita_total')
    
    # Calcular lucro e margem para cada produto
    resumo_list = []
    receita_total = 0
    custo_total = 0
    lucro_total = 0
    
    for item in resumo_produtos:
        custo = (item['produto__preco_custo'] or 0) * item['quantidade_vendida']
        lucro = item['receita_total'] - custo
        margem = (lucro * 100 / item['receita_total']) if item['receita_total'] > 0 else 0
        
        resumo_list.append({
            'produto__nome': item['produto__nome'],
            'quantidade_vendida': item['quantidade_vendida'],
            'receita_total': item['receita_total'],
            'custo_total': custo,
            'lucro_total': lucro,
            'margem_lucro': margem
        })
        
        receita_total += item['receita_total']
        custo_total += custo
        lucro_total += lucro
    
    # Ordenar por lucro
    resumo_list.sort(key=lambda x: x['lucro_total'], reverse=True)
    
    margem_lucro_geral = (lucro_total * 100 / receita_total) if receita_total > 0 else 0
    
    # Criar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph('VendaFácil PDV', title_style))
    elements.append(Paragraph(f'Relatório de Lucratividade', styles['Heading2']))
    elements.append(Paragraph(f'Período: {data_inicio} a {data_fim}', styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Estatísticas gerais
    stats_data = [
        ['Receita Total:', f'R$ {receita_total:,.2f}'],
        ['Custo Total:', f'R$ {custo_total:,.2f}'],
        ['Lucro Total:', f'R$ {lucro_total:,.2f}'],
        ['Margem de Lucro:', f'{margem_lucro_geral:.1f}%'],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#d4edda')),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 30))
    
    # Tabela de produtos
    elements.append(Paragraph('Lucratividade por Produto', styles['Heading3']))
    elements.append(Spacer(1, 10))
    
    produtos_data = [['Produto', 'Qtd', 'Receita', 'Custo', 'Lucro', 'Margem']]
    for item in resumo_list:
        produtos_data.append([
            item['produto__nome'][:25],
            str(int(item['quantidade_vendida'])),
            f"R$ {item['receita_total']:,.2f}",
            f"R$ {item['custo_total']:,.2f}",
            f"R$ {item['lucro_total']:,.2f}",
            f"{item['margem_lucro']:.1f}%"
        ])
    
    produtos_table = Table(produtos_data, colWidths=[2*inch, 0.6*inch, 1.1*inch, 1.1*inch, 1.1*inch, 0.7*inch])
    produtos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(produtos_table)
    
    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_lucratividade_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response
