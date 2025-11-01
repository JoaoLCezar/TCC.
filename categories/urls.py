from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('', views.listar_categorias, name='listar_categorias'),
    
    path('nova/', views.criar_categoria, name='criar_categoria'),
    
]