from .models import SessaoCaixa

def verificar_caixa_aberto(request):
    if not request.user.is_authenticated:
        return {'sessao_caixa_aberta': None}

    try:
        sessao = SessaoCaixa.objects.get(usuario=request.user, status='ABERTO')
        return {'sessao_caixa_aberta': sessao}
    except SessaoCaixa.DoesNotExist:
        return {'sessao_caixa_aberta': None}