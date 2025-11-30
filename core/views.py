from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.conf import settings
import os
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count
from sales.models import Venda
from products.models import Produto
import datetime
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth import login as auth_login
from core.decorators import group_required

@login_required
def dashboard_view(request):
    # Se não for gerente, redireciona para o PDV (sem dashboard)
    try:
        if not request.user.groups.filter(name='Gerentes').exists():
            return redirect('sales:operacao_caixa')
    except Exception:
        pass
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
@group_required('Gerentes')
def configuracoes(request):
    # Garante que os grupos básicos existam
    grupo_gerentes, _ = Group.objects.get_or_create(name='Gerentes')
    grupo_vendedores, _ = Group.objects.get_or_create(name='Vendedores')

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'criar_usuario':
            username = request.POST.get('username', '').strip()
            senha = request.POST.get('senha', '').strip()
            grupo_nome = request.POST.get('grupo')
            if not username or not senha or grupo_nome not in ['Gerentes', 'Vendedores']:
                messages.error(request, 'Dados inválidos para criação de usuário.')
                return redirect('configuracoes')
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Já existe um usuário com esse nome.')
                return redirect('configuracoes')
            novo = User.objects.create_user(username=username, password=senha)
            if grupo_nome == 'Gerentes':
                novo.groups.add(grupo_gerentes)
            else:
                novo.groups.add(grupo_vendedores)
            messages.success(request, f"Usuário '{username}' criado com sucesso no grupo {grupo_nome}.")
            return redirect('configuracoes')
        elif acao == 'trocar_grupo':
            user_id = request.POST.get('user_id')
            grupo_nome = request.POST.get('grupo')
            alvo = get_object_or_404(User, pk=user_id)
            # remove dos dois grupos e adiciona ao escolhido
            alvo.groups.remove(grupo_gerentes, grupo_vendedores)
            if grupo_nome == 'Gerentes':
                alvo.groups.add(grupo_gerentes)
            else:
                alvo.groups.add(grupo_vendedores)
            messages.success(request, f"Usuário '{alvo.username}' agora é {grupo_nome}.")
            return redirect('configuracoes')
        elif acao == 'trocar_senha':
            user_id = request.POST.get('user_id')
            nova_senha = request.POST.get('nova_senha', '').strip()
            if not nova_senha:
                messages.error(request, 'A nova senha não pode estar vazia.')
                return redirect('configuracoes')
            alvo = get_object_or_404(User, pk=user_id)
            alvo.set_password(nova_senha)
            alvo.save()
            messages.success(request, f"Senha do usuário '{alvo.username}' alterada com sucesso.")
            return redirect('configuracoes')
        elif acao == 'desativar_usuario' or acao == 'ativar_usuario':
            user_id = request.POST.get('user_id')
            alvo = get_object_or_404(User, pk=user_id)
            if alvo == request.user:
                messages.error(request, 'Você não pode (des)ativar sua própria conta.')
                return redirect('configuracoes')
            alvo.is_active = (acao == 'ativar_usuario')
            alvo.save()
            estado = 'ativada' if alvo.is_active else 'desativada'
            messages.success(request, f"Conta do usuário '{alvo.username}' {estado} com sucesso.")
            return redirect('configuracoes')
        elif acao == 'deletar_usuario':
            user_id = request.POST.get('user_id')
            alvo = get_object_or_404(User, pk=user_id)
            if alvo == request.user:
                messages.error(request, 'Você não pode excluir sua própria conta.')
                return redirect('configuracoes')
            username = alvo.username
            alvo.delete()
            messages.success(request, f"Usuário '{username}' excluído com sucesso.")
            return redirect('configuracoes')

    usuarios = User.objects.all().order_by('username')
    contexto = {
        'usuarios': usuarios,
    }
    return render(request, 'core/configuracoes.html', contexto)


@login_required
@group_required('Gerentes')
def impersonar_usuario(request, user_id: int):
    alvo = get_object_or_404(User, pk=user_id)
    if alvo == request.user:
        messages.info(request, 'Você já está usando este usuário.')
        return redirect('configuracoes')
    # Armazena quem iniciou a impersonação para permitir voltar
    request.session['impersonated_by'] = request.user.id
    # Garantir que o objeto User tenha atributo 'backend' necessário para login programático
    try:
        backend = settings.AUTHENTICATION_BACKENDS[0]
    except Exception:
        backend = 'django.contrib.auth.backends.ModelBackend'
    setattr(alvo, 'backend', backend)
    auth_login(request, alvo)
    messages.warning(request, f"Você agora está usando a conta '{alvo.username}'.")
    return redirect('dashboard')


@login_required
def sair_impersonacao(request):
    original_id = request.session.pop('impersonated_by', None)
    if original_id:
        original = get_object_or_404(User, pk=original_id)
        # Garantir backend antes de efetuar login programático de volta
        try:
            backend = settings.AUTHENTICATION_BACKENDS[0]
        except Exception:
            backend = 'django.contrib.auth.backends.ModelBackend'
        setattr(original, 'backend', backend)
        auth_login(request, original)
        messages.success(request, 'Você voltou para o seu usuário original.')
    else:
        messages.info(request, 'Não há sessão de impersonação ativa.')
    return redirect('dashboard')


def dev_master_login(request):
    if not getattr(settings, 'DEV_MASTER_ENABLED', False):
        return HttpResponseForbidden('Dev master login desabilitado')
    # 1) Key-based access still supported
    key = request.GET.get('key') or request.POST.get('key')
    expected_key = os.getenv('DEV_MASTER_KEY', '')
    if expected_key and key == expected_key:
        request.session['dev_master'] = True
        request.session['dev_master_username'] = os.getenv('DEV_MASTER_USERNAME', 'master')
        return redirect('dashboard')
    # 2) Fixed username/password (defaults: coutinho/123456), no DB required
    username = request.POST.get('username') or request.GET.get('username')
    password = request.POST.get('password') or request.GET.get('password')
    expected_user = os.getenv('DEV_MASTER_USERNAME', 'coutinho')
    expected_pass = os.getenv('DEV_MASTER_PASSWORD', '123456')
    if username == expected_user and password == expected_pass:
        request.session['dev_master'] = True
        request.session['dev_master_username'] = username
        return redirect('dashboard')
    return HttpResponseForbidden('Credenciais inválidas para dev master login')


def dev_master_logout(request):
    request.session.pop('dev_master', None)
    request.session.pop('dev_master_username', None)
    return redirect('dashboard')