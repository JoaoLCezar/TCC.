from django.urls import path
from . import views


app_name = 'suppliers'

urlpatterns = [
    path('', views.listar_fornecedores, name='listar_fornecedores'),

    path('nome/', views.criar_fornecedor, name='criar_fornecedor'),

    path('<int:pk>/editar/', views.atualizar_fornecedor, name='atualizar_fornecedor'),

    path('<int:pk>/excluir/', views.excluir_fornecedor, name='excluir_fornecedor'),
]