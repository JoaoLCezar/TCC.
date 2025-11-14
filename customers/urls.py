from django.urls import path
from . import views


app_name = 'customers'

urlpatterns = [
    path('', views.listar_clientes, name='listar_clientes'),

    path('novo/', views.criar_cliente, name='criar_cliente'),

    path('<int:pk>/editar/', views.atualizar_cliente, name='atualizar_cliente'),

    path('<int:pk>/excluir/', views.excluir_cliente, name='excluir_cliente'),

    path('api/buscar/', views.api_buscar_clientes, name='api_buscar_clientes'),
]