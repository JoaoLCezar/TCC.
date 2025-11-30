import os
from django.conf import settings


class DevMasterUser:
    is_authenticated = True
    is_active = True
    is_staff = True
    is_superuser = True
    id = 0
    pk = 0

    def __init__(self, username="master", email="master@example.com"):
        self.username = username
        self.email = email

    def get_username(self):
        return self.username


class DevMasterMiddleware:
    """
    If DEV_MASTER_ENABLED=1 and session flag 'dev_master' is set,
    force request.user to a DevMasterUser (no DB access required).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if getattr(settings, 'DEV_MASTER_ENABLED', False) and request.session.get('dev_master'):
                username = request.session.get('dev_master_username') or os.getenv('DEV_MASTER_USERNAME', 'master')
                email = os.getenv('DEV_MASTER_EMAIL', 'master@example.com')
                request.user = DevMasterUser(username=username, email=email)
        except Exception:
            # Be fail-safe: never break request flow in dev
            pass
        return self.get_response(request)
