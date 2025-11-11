from django.db import models


class Fornecedor(models.Model):
    nome_fantasia = models.CharField(
        max_length=255,
        verbose_name="Nome Fantasia"
    )

    razao_social = models.CharField(
        max_length=255,
        verbose_name="Razão Social",
        null=True,
        blank=True
    )

    cnpj = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="CNPJ",
    )

    email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="E-mail de Contato"
    )

    telefone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Telefone(ex: +55 21 99999-8888)"
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro"
    )

    class Meta:
        ordering = ('nome_fantasia',)
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome_fantasia