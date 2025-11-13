from django.db import models
from categories.models import Categoria
from django.contrib.auth.models import User

    
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
    
class MovimentoEstoque(models.Model):
    TIPO_MOVIMENTO_CHOICE = [
        ('ENTRADA', 'Entrada (Manual/Compra)'),
        ('SAIDA_VENDA', 'Saída (Venda PDV)'),
        ('AJUSTE_PERDA', 'Ajuste (Perda/Dano)'),
        ('AJUSTE_CONTAGEM', 'Ajuste (Contagem de Estoque)'),
    ]

    produto = models.ForeignKey(
        Produto,
        on_delete = models.CASCADE,
        related_name="movimentos"
    )

    quantidade = models.IntegerField(
        help_text="Quantidade a ser movimentada. Use negativos para saídas/perdas."
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMENTO_CHOICE,
        default='ENTRADA'
    )

    data_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data e Hora do Movimento"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    motivo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Motivo do ajuste ou nº da nota fiscal de entrada."
    )

    class Meta:
        ordering = ['-data_hora']
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"

    def __str__(self):
        sinal = '+' if self.quantidade > 0 else ''
        return f"{self.get_tipo_display()}: {sinal}{self.quantidade} de {self.produto.nome}"


