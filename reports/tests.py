from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from decimal import Decimal

from sales.models import SessaoCaixa, Venda, ItemVenda, MovimentoCaixa
from products.models import Produto


class ReportsBaseTestCase(TestCase):
	def setUp(self):
		# Groups and user
		self.grp_gerentes, _ = Group.objects.get_or_create(name='Gerentes')
		self.user = User.objects.create_user('gerente', password='123')
		self.user.groups.add(self.grp_gerentes)

		# Products
		self.p1 = Produto.objects.create(nome='A', preco=Decimal('50.00'), preco_custo=Decimal('30.00'), estoque=100)
		self.p2 = Produto.objects.create(nome='B', preco=Decimal('100.00'), preco_custo=Decimal('70.00'), estoque=100)


class RelatorioCaixaSessaoTests(ReportsBaseTestCase):
	def test_esperado_de_fechamento_por_sessao(self):
		self.client.login(username='gerente', password='123')
		sessao = SessaoCaixa.objects.create(usuario=self.user, valor_inicial=Decimal('200.00'))

		# Vendas na sessão: 1 em dinheiro (150), 1 em crédito (100)
		v1 = Venda.objects.create(usuario=self.user, status='CONCLUIDA', sessao=sessao, forma_pagamento='DINHEIRO', valor_total=Decimal('150.00'))
		v2 = Venda.objects.create(usuario=self.user, status='CONCLUIDA', sessao=sessao, forma_pagamento='CREDITO', valor_total=Decimal('100.00'))

		# Movimentos: suprimento 50, sangria 30
		MovimentoCaixa.objects.create(sessao=sessao, usuario=self.user, tipo='SUPRIMENTO', valor=Decimal('50.00'))
		MovimentoCaixa.objects.create(sessao=sessao, usuario=self.user, tipo='SANGRIA', valor=Decimal('30.00'))

		url = reverse('reports:relatorio_caixa') + f'?sessao_id={sessao.id}'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# esperado = abertura (200) + dinheiro (150) + suprimentos (50) - sangrias (30) = 370
		self.assertEqual(resp.context['esperado_final'], Decimal('370.00'))


class RelatorioLucratividadeTests(ReportsBaseTestCase):
	def test_aggregates_lucro_e_margem(self):
		self.client.login(username='gerente', password='123')
		# Vendas concluídas com itens
		v = Venda.objects.create(usuario=self.user, status='CONCLUIDA')
		ItemVenda.objects.create(venda=v, produto=self.p1, quantidade=2, preco_unitario=self.p1.preco, subtotal=Decimal('100.00'))
		ItemVenda.objects.create(venda=v, produto=self.p2, quantidade=1, preco_unitario=self.p2.preco, subtotal=Decimal('100.00'))

		# Receita total = 200; Custo total = 2*30 + 1*70 = 130; Lucro = 70; Margem = 70/200 = 35%
		url = reverse('reports:relatorio_lucratividade')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.context['receita_total'], Decimal('200.00'))
		self.assertEqual(resp.context['custo_total'], Decimal('130.00'))
		self.assertEqual(resp.context['lucro_total'], Decimal('70.00'))
		self.assertAlmostEqual(float(resp.context['margem_lucro_geral']), 35.0, places=2)

