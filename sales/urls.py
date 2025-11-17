from django.urls import path
from . import views


app_name = 'sales'

urlpatterns = [
    path('caixa/', views.operacao_caixa, name='operacao_caixa'),

    path('processar/', views.processar_venda, name='processar_venda'),

    path('historico/', views.historico_vendas, name='historico_vendas'),

    path('<int:pk>/detalhe/', views.detalhe_venda, name='detalhe_venda'),

    path('cancelar/', views.cancelar_venda, name='cancelar_venda'),

    path('abrir-caixa/', views.abrir_caixa, name='abrir_caixa'),

    path('fechar-caixa/', views.fechar_caixa, name='fechar_caixa'),

    path('sessao/<int:pk>/relatorio/', views.relatorio_sessao, name='relatorio_sessao'),
    
    path('sessoes/', views.listar_sessoes, name='listar_sessoes'),

    path('sessao/<int:pk>/pdf/', views.gerar_relatorio_pdf, name='gerar_relatorio_pdf'),
]