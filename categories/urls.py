from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('', views.listar_categorias, name='listar_categorias'),
    
    path('nova/', views.criar_categoria, name='criar_categoria'),

    path('<int:pk>/editar/', views.atualizar_categoria, name='atualizar_categoria'),
    
    path('<int:pk>/excluir/', views.excluir_categoria, name='excluir_categoria'),
]