from django.conf import settings


def dados_empresa(request):
    return {
        'EMPRESA_NOME': getattr(settings, 'EMPRESA_NOME', 'VendaFácil'),
        'EMPRESA_ENDERECO': getattr(settings, 'EMPRESA_ENDERECO', ''),
        'EMPRESA_TELEFONE': getattr(settings, 'EMPRESA_TELEFONE', ''),
        'EMPRESA_CNPJ': getattr(settings, 'EMPRESA_CNPJ', ''),
    }
