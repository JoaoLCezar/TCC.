from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.listar_produtos, name='listar_produtos'),
]

