from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.listar_produtos, name='listar_produtos'),

    path('<int:pk>/', views.detalhe_produto, name='detalhe_produto'),

    #Rota para criar NovoProduto
    path('novo/', views.criar_produto, name='criar_produto'),

    #Rota para atualizar produto
    path('<int:pk>/editar/', views.atualizar_produto, name='atualizar_produto'),

    #Rota para Excluir produto
    path('<int:pk>/excluir/', views.excluir_produto, name='excluir_produto'),

    path('<int:pk>/movimentos/', views.historico_movimentos, name='historico_movimentos'),
    
    ]

