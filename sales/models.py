from django.db import models
from django.contrib.auth.models import User
from products.models import Produto

# Create your models here.
class Venda(models.Model):
    STATUS_CHOICES = [
        ('CONCLUIDA', 'Concluida'),
        ('CANCELADA', 'Cancelada'),
    ]

    data_hora = models.DateTimeField(
        auto_now_add= True,
        verbose_name="Data e Hora da Venda"
    )

    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Valor total do recibo"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CONCLUIDA'
    )


    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendas',
        verbose_name="Vendedor"
    )

    class Meta:
        ordering = ['-data_hora']
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"

    def __str__(self):
        return f"Venda #{self.pk} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
    

class ItemVenda(models.Model):
    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name='itens'
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='itens_vendidos'
    )

    quantidade = models.PositiveIntegerField(
        default=1,
        help_text="Quantidade vendida"
    )


    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço Unitário na Venda"
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    def save(self, *args, **kwargs):
        self.subtotal = self.preco_unitario * self.quantidade
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} @ R${self.preco_unitario}"