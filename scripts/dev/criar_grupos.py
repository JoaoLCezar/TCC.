import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import Group, User

# Criar grupos
gerentes, created_g = Group.objects.get_or_create(name='Gerentes')
vendedores, created_v = Group.objects.get_or_create(name='Vendedores')

if created_g:
    print("Grupo 'Gerentes' criado!")
else:
    print("Grupo 'Gerentes' já existe.")

if created_v:
    print("Grupo 'Vendedores' criado!")
else:
    print("Grupo 'Vendedores' já existe.")

# Adicionar admin aos grupos
user = User.objects.get(username='admin')
user.groups.add(gerentes)
user.groups.add(vendedores)

print(f"\nUsuário 'admin' adicionado aos grupos:")
for group in user.groups.all():
    print(f"  - {group.name}")

print("\n✅ Configuração concluída!")
