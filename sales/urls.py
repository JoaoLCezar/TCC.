from django.urls import path
from . import views


app_name = 'sales'

urlpatterns = [
    path('caixa/', views.operacao_caixa, name='operacao_caixa'),

    path('processar/', views.processar_venda, name='processar_venda'),

    path('movimento-caixa/', views.registrar_movimento_caixa, name='registrar_movimento_caixa'),

    path('historico/', views.historico_vendas, name='historico_vendas'),

    path('<int:pk>/detalhe/', views.detalhe_venda, name='detalhe_venda'),

    path('<int:venda_id>/recibo/', views.imprimir_recibo, name='imprimir_recibo'),
    path('<int:venda_id>/devolucao/', views.registrar_devolucao, name='registrar_devolucao'),
    path('<int:venda_id>/cancelar/', views.cancelar_venda_existente, name='cancelar_venda_existente'),

    path('cancelar/', views.cancelar_venda, name='cancelar_venda'),

    path('abrir-caixa/', views.abrir_caixa, name='abrir_caixa'),

    path('fechar-caixa/', views.fechar_caixa, name='fechar_caixa'),
]