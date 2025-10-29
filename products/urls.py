from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.listar_produtos, name='listar_produtos'),

    path('<int:pk>/', views.detalhe_produto, name='detalhe_produto'),

    #Rota para criar NovoProduto
    path('novo/', views.criar_produto, name='criar_produto'),
]

