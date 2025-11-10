from django.db import models

class Cliente(models.Model):
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome Completo"
    )

    email = models.EmailField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name="E-mail"
    )

    telefone = models.CharField(
        max_length=17,
        null=True,
        blank=True,
        verbose_name="Telefone"
    )

    documento = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="CPF"
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro"
    )

    class Meta:
        ordering = ('nome',)
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nome