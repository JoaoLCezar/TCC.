from functools import wraps
from django.shortcuts import redirect, render
from django.conf import settings


def group_required(*group_names):
    """
    Decorator que restringe o acesso de uma view a utilizadores que
    pertençam a pelo menos um dos grupos informados.

    - Se o utilizador não estiver autenticado: redireciona para a página de login.
    - Se o utilizador estiver autenticado mas não pertencer aos grupos: renderiza
      `core/permission_denied.html` com status 403.

    Uso: @group_required('Gerentes', 'Vendedores')
    """

    login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            # Se não autenticado, envia para login com next
            if not user or not getattr(user, 'is_authenticated', False):
                return redirect(f"{login_url}?next={request.path}")

            # Superusers/staff devem ter acesso completo
            if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
                return view_func(request, *args, **kwargs)

            # Se pertence a um dos grupos permitidos, executa a view
            if user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)

            # Está autenticado mas não tem permissão: mostrar página 403 personalizada
            context = {
                'required_groups': group_names,
            }
            return render(request, 'core/permission_denied.html', context=context, status=403)

        return _wrapped_view

    return decorator
        