from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def group_required(*group_names):
    """
    Decorator (regra) que restringe o acesso de uma view
    a utilizadores que pertençam a grupos específicos.
    
    Ex: @group_required('Gerentes', 'Vendedores')
    """

    def check_groups(user):
        # Verifica se o utilizador está logado (se não estiver, não tem grupos)
        if not user.is_authenticated:
            return False
        
        # Verifica se o utilizador pertence a pelo menos um grupo
        if user.groups.filter(name__in=group_names).exists():
            return True
        
        # Se não pertencer a nenhum, é bloqueado.
        return False
        
    
    return user_passes_test(check_groups, login_url='/accounts/login/')
        