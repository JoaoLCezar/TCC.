from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.menu_relatorios, name='menu_relatorios'),
    path('caixa/', views.relatorio_caixa, name='relatorio_caixa'),
    path('caixa/pdf/', views.relatorio_caixa_pdf, name='relatorio_caixa_pdf'),
    path('vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    path('vendas/pdf/', views.relatorio_vendas_pdf, name='relatorio_vendas_pdf'),
    path('produtos/', views.relatorio_produtos, name='relatorio_produtos'),
    path('produtos/pdf/', views.relatorio_produtos_pdf, name='relatorio_produtos_pdf'),
    path('estoque/', views.relatorio_estoque, name='relatorio_estoque'),
    path('estoque/pdf/', views.relatorio_estoque_pdf, name='relatorio_estoque_pdf'),
    path('clientes/', views.relatorio_clientes, name='relatorio_clientes'),
    path('clientes/pdf/', views.relatorio_clientes_pdf, name='relatorio_clientes_pdf'),
    path('lucratividade/', views.relatorio_lucratividade, name='relatorio_lucratividade'),
    path('lucratividade/pdf/', views.relatorio_lucratividade_pdf, name='relatorio_lucratividade_pdf'),
]
