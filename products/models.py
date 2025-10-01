from django.db import models

# Create your models here.
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True, help_text="Nome da categoria")

    def __str__(self):
        return self.nome
    
class Produto(models.Model):
    nome = models.CharField(max_length=200, help_text="Nome do produto")
    descricao = models.TextField(blank=True, null=True, help_text="Descrição do Produto")
    preco = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço do produto")
    estoque = models.IntegerField(default=0, help_text="Quantidade em estoque")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='produtos', help_text="Categoria do produto")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome