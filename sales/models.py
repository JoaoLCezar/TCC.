from django.db import models
from django.contrib.auth.models import User
from products.models import Produto
from customers.models import Cliente
from django.utils import timezone


class SessaoCaixa(models.Model):
    STATUS_CHOICE = [
        ('ABERTO', 'Aberto'),
        ('FECHADO', 'Fechado'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT, # Protege o histórico
        related_name="sessoes_caixa",
        verbose_name="Operador"
    )

    data_abertura = models.DateTimeField(
        default=timezone.now, # Define a hora atual quando é criado
        verbose_name="Data de Abertura"
    )

    valor_inicial = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor Inicial (Suprimento)"
    )

    
    data_fechamento = models.DateTimeField(   # Estes campos começam vazios (nulos)
        null=True, 
        blank=True,
        verbose_name="Data de Fechamento"
    )

    valor_final_informado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="Valor Final (Informado pelo Operador)"
    )

    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICE, 
        default='ABERTO'
    )

    class Meta:
        ordering = ['-data_abertura']
        verbose_name = "Sessão de Caixa"
        verbose_name_plural = "Sessões de Caixa"

    def __str__(self):
        # Ex: "Sessão #1 (admin) - 08/11/2025"
        return f"Sessão #{self.pk} ({self.usuario.username}) - {self.data_abertura.strftime('%d/%m/%Y')}"


class Venda(models.Model):
    STATUS_CHOICES = [
        ('CONCLUIDA', 'Concluida'),
        ('CANCELADA', 'Cancelada'),
    ]

    PAGAMENTO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('CREDITO', 'Cartão de Crédito'),
        ('DEBITO', 'Cartão de Débito'),
        ('PIX', 'PIX'),
    ]


    data_hora = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONCLUIDA')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas', verbose_name="Vendedor")
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    sessao = models.ForeignKey(SessaoCaixa, on_delete=models.PROTECT, related_name="vendas_na_sessao", null=True, blank=True)

    forma_pagamento = models.CharField(
        max_length=20, 
        choices=PAGAMENTO_CHOICES, 
        default='DINHEIRO',
        verbose_name="Forma de Pagamento"
    )

    sessao = models.ForeignKey(
        SessaoCaixa,
        on_delete=models.PROTECT,
        related_name="vendas_na_sessao",
        null=True,
        blank=True
    )


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

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compras'
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