from django.db import models

# Create your models here.
class Categoria(models.Model):
    nome = models.CharField(
        max_length= 100,
        unique=True, #Não permite repetições
        help_text="Nome da Categoria (ex: Bebidas, Limpeza, Doces)"
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )

    class Meta:
        ordering = ('nome',)

        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome