# VendaFácil PDV — TCC

Sistema de Ponto de Venda (PDV) em Django com: abertura/fechamento de caixa, movimentos (suprimento/sangria), vendas com desconto (valor/%), troco apenas em dinheiro, recibo, cancelamento de venda com recomposição de estoque, e relatórios (Caixa, Vendas, Produtos, Estoque, Clientes, Lucratividade) em HTML e PDF.

## Requisitos

- Python 3.11+
- Django 5.x
- SQLite (dev) — já incluso como `db.sqlite3`

## Instalação (Windows PowerShell)

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Migrar banco e (opcional) popular dados
python manage.py migrate
python manage.py createsuperuser
# opcional: script de popular dados
python popular_banco.py

# Rodar servidor
python manage.py runserver
```

## Login e Perfis

- Grupos: `Gerentes` e `Vendedores` (controle de acesso por grupos).
- Crie um usuário gerente e associe ao grupo `Gerentes` para acessar relatórios e detalhes de vendas.

## Principais Funcionalidades

- PDV: carrinho por produto, desconto valor/% no total, valor recebido e troco (troco apenas quando `DINHEIRO`).
- Caixa: abertura/fechamento, movimentos de `SUPRIMENTO` e `SANGRIA`.
- Relatórios: filtros por período/sessão; HTML e PDF; lucratividade com receita, custo, lucro, margem por produto.
- Pós-venda: cancelar venda (repõe estoque e marca status `CANCELADA`).
- Acesso: telas gerenciais restritas a `Gerentes`.

## Roteiro de Demonstração (7–10 min)

1. Login como Gerente → abrir caixa (suprimento).
2. PDV: realizar 2 vendas (uma com dinheiro + desconto, outra com cartão). Mostrar troco apenas em dinheiro e imprimir recibo.
3. Registrar suprimento e sangria no caixa.
4. Histórico de vendas (somente Gerentes) → abrir uma venda e cancelar (estoque reposto).
5. Relatório de Caixa: esperado de fechamento = abertura + recebido em dinheiro + suprimentos − sangrias.
6. Relatório de Lucratividade: receita, custo, lucro, margem por produto; exportar PDF.

## Testes

Executar toda a suíte:

```
python manage.py test
```

Testes cobrem:

- Cálculo de desconto percentual/valor ao processar venda.
- Cancelamento de venda repõe estoque e altera status.
- Fechamento esperado do caixa por sessão.
- Agregados de lucratividade (receita, custo, lucro, margem).

## Observações

- O fluxo de “Devolução” foi simplificado para “Cancelar Venda” por clareza operacional. Pontos futuros: devolução parcial por item e exportação CSV dos relatórios.
