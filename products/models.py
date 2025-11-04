from django.db import models
from categories.models import Categoria

# Create your models here.
    
class Produto(models.Model):
    nome = models.CharField(max_length=200, help_text="Nome do produto")
    descricao = models.TextField(blank=True, null=True, help_text="Descrição do Produto")
    preco = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço do produto")
    estoque = models.IntegerField(default=0, help_text="Quantidade em estoque")
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome