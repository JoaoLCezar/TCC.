from django.urls import path
from . import views


app_name = 'sales'

urlpatterns = [
    path('caixa/', views.operacao_caixa, name='operacao_caixa'),

    path('processar/', views.processar_venda, name='processar_venda'),
]