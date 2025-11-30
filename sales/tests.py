from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from decimal import Decimal

from products.models import Produto, MovimentoEstoque
from .models import SessaoCaixa, Venda, ItemVenda


class BaseTestCase(TestCase):
	def setUp(self):
		# Ensure groups exist
		self.grp_gerentes, _ = Group.objects.get_or_create(name='Gerentes')
		self.grp_vendedores, _ = Group.objects.get_or_create(name='Vendedores')

		# Users
		self.user_gerente = User.objects.create_user('gerente', password='123')
		self.user_gerente.groups.add(self.grp_gerentes)

		self.user_vendedor = User.objects.create_user('vendedor', password='123')
		self.user_vendedor.groups.add(self.grp_vendedores)

		# Product
		self.prod = Produto.objects.create(
			nome='Produto X', preco=Decimal('100.00'), preco_custo=Decimal('60.00'), estoque=50
		)


class ProcessarVendaDescontoTests(BaseTestCase):
	def setUp(self):
		super().setUp()
		# Open a session for vendedor
		self.sessao = SessaoCaixa.objects.create(usuario=self.user_vendedor, valor_inicial=Decimal('200.00'))

	def test_desconto_percentual_aplicado(self):
		self.client.login(username='vendedor', password='123')
		url = reverse('sales:processar_venda')
		payload = {
			'carrinho': {str(self.prod.id): {'quantidade': 2}},
			'cliente_id': None,
			'forma_pagamento': 'DINHEIRO',
			'desconto_tipo': 'percentual',
			'desconto_input': 10,  # 10%
		}
		resp = self.client.post(url, data=payload, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('sucesso'))
		venda = Venda.objects.get(pk=data['venda_id'])
		# 2 x 100 = 200; 10% desconto = 20; total esperado = 180
		self.assertEqual(venda.valor_total, Decimal('180.00'))

	def test_desconto_valor_aplicado(self):
		self.client.login(username='vendedor', password='123')
		url = reverse('sales:processar_venda')
		payload = {
			'carrinho': {str(self.prod.id): {'quantidade': 3}},
			'cliente_id': None,
			'forma_pagamento': 'PIX',
			'desconto_tipo': 'valor',
			'desconto_input': 50,  # R$ 50
		}
		resp = self.client.post(url, data=payload, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('sucesso'))
		venda = Venda.objects.get(pk=data['venda_id'])
		# 3 x 100 = 300; -50 = 250
		self.assertEqual(venda.valor_total, Decimal('250.00'))


class CancelarVendaTests(BaseTestCase):
	def setUp(self):
		super().setUp()
		# Create a concluded sale with 4 units
		self.venda = Venda.objects.create(usuario=self.user_gerente, status='CONCLUIDA', forma_pagamento='DINHEIRO')
		ItemVenda.objects.create(
			venda=self.venda, produto=self.prod, quantidade=4, preco_unitario=self.prod.preco, subtotal=Decimal('400.00')
		)
		# Reduce stock as if sold
		self.prod.estoque -= 4
		self.prod.save()

	def test_cancelar_venda_repõe_estoque_e_altera_status(self):
		estoque_antes = self.prod.estoque
		self.client.login(username='gerente', password='123')
		url = reverse('sales:cancelar_venda_existente', args=[self.venda.id])
		resp = self.client.post(url, data={'motivo': 'Erro de lançamento'})
		self.assertEqual(resp.status_code, 302)  # redirect
		self.venda.refresh_from_db()
		self.prod.refresh_from_db()
		self.assertEqual(self.venda.status, 'CANCELADA')
		self.assertEqual(self.prod.estoque, estoque_antes + 4)
		# Movimento de estoque criado
		self.assertTrue(MovimentoEstoque.objects.filter(produto=self.prod, tipo='ENTRADA').exists())

