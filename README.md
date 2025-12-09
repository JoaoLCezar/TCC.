# VendaFácil PDV — Sistema de Gestão de Vendas

Sistema de Ponto de Venda (PDV) e gestão de estoque desenvolvido em Django para o Trabalho de Conclusão de Curso (TCC). O sistema oferece controle completo de vendas, caixa, produtos, clientes, fornecedores e relatórios gerenciais.

## 📋 Funcionalidades Principais

### PDV (Ponto de Venda)
- Registro de vendas com múltiplos produtos
- Desconto por valor (R$) ou percentual (%)
- Cálculo automático de troco (apenas para pagamento em dinheiro)
- Múltiplas formas de pagamento (Dinheiro, Débito, Crédito, PIX)
- Emissão de recibo de venda
- Consulta rápida por código de barras

### Gestão de Caixa
- Abertura e fechamento de sessões de caixa
- Movimentos de suprimento e sangria
- Relatório de fechamento com saldo esperado
- Histórico completo de todas as sessões

### Gestão de Produtos
- Cadastro com imagem e código de barras
- Controle de estoque automático
- Histórico de movimentações de estoque
- Categorização de produtos
- Ajustes manuais de estoque

### Gestão de Clientes e Fornecedores
- Cadastro completo com dados de contato
- Vínculo de vendas a clientes
- Histórico de compras por cliente

### Relatórios Gerenciais
- Relatório de Caixa (saldos, movimentos)
- Relatório de Vendas (período, produto, cliente)
- Relatório de Estoque (disponibilidade, movimentos)
- Relatório de Lucratividade (receita, custo, lucro, margem)
- Exportação em HTML e PDF

### Controle de Acesso
- Autenticação de usuários
- Grupos de permissão (Gerentes e Vendedores)
- Restrição de acesso a relatórios e operações sensíveis

## 🛠️ Stack Técnica

- **Framework**: Django 5.x
- **Linguagem**: Python 3.11+
- **Banco de Dados**: PostgreSQL (produção)
- **Frontend**: Templates Django + CSS
- **Autenticação**: Django Auth System

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.11 ou superior
- PostgreSQL 
- Git

### Instalação (Windows PowerShell)

1. **Clone o repositório**
```powershell
git clone https://github.com/JoaoLCezar/TCC.git
cd TCC
```

2. **Crie e ative o ambiente virtual**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. **Instale as dependências**
```powershell
pip install -r requirements.txt
```

4. **Configure o banco de dados**

Edite `core/settings.py` se necessário. Por padrão está configurado para PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'venda_facil_db',
        'USER': 'postgres',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}
```

Para usar SQLite (desenvolvimento), altere para:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

5. **Execute as migrações**
```powershell
python manage.py migrate
```

6. **Crie um superusuário**
```powershell
python manage.py createsuperuser
```

7. **(Opcional) Popular banco com dados de teste**
```powershell
python scripts/popular_banco.py
```

8. **Execute o servidor de desenvolvimento**
```powershell
python manage.py runserver
```

Acesse: `http://127.0.0.1:8000/`

### Configuração de Usuários e Permissões

1. Acesse o Django Admin: `http://127.0.0.1:8000/admin/`
2. Crie os grupos `Gerentes` e `Vendedores`
3. Associe usuários aos grupos conforme suas funções:
   - **Gerentes**: acesso completo a relatórios e configurações
   - **Vendedores**: acesso ao PDV e cadastros básicos

## 📱 Como Usar

### Fluxo Básico de Operação

1. **Login no sistema** com suas credenciais
2. **Abrir caixa** informando o saldo inicial
3. **Registrar vendas** no PDV:
   - Adicionar produtos (busca ou código de barras)
   - Aplicar descontos se necessário
   - Selecionar forma de pagamento
   - Informar cliente (opcional)
   - Finalizar venda
4. **Realizar movimentos** (suprimento/sangria) se necessário
5. **Fechar caixa** ao final do expediente

### Demonstração Rápida (7-10 minutos)

1. **Login como Gerente** → Abrir caixa com saldo inicial
2. **Realizar vendas no PDV**:
   - Venda 1: Pagamento em dinheiro com desconto (mostra cálculo de troco)
   - Venda 2: Pagamento com cartão (sem troco)
   - Imprimir recibo de venda
3. **Movimentos de caixa**:
   - Registrar suprimento (entrada de dinheiro)
   - Registrar sangria (saída de dinheiro)
4. **Gestão de vendas** (apenas Gerentes):
   - Visualizar histórico de vendas
   - Cancelar uma venda (estoque é automaticamente reposto)
5. **Relatórios**:
   - Relatório de Caixa: verificar saldo esperado
   - Relatório de Lucratividade: visualizar receita, custo, lucro e margem
   - Exportar relatórios em PDF

## 📂 Estrutura do Projeto

```
TCC/
├── categories/         # App de categorias de produtos
├── core/              # Configurações do projeto Django
├── customers/         # App de gestão de clientes
├── docs/              # Documentação (casos de uso, diagramas)
├── products/          # App de produtos e estoque
├── sales/             # App de vendas e caixa
├── suppliers/         # App de fornecedores
├── static/            # Arquivos estáticos (CSS, JS, imagens)
├── templates/         # Templates HTML
├── scripts/           # Scripts auxiliares
├── reports/           # Relatórios gerados
├── manage.py          # Gerenciador Django
└── requirements.txt   # Dependências Python
```

## 🧪 Testes

Execute a suíte completa de testes:

```powershell
python manage.py test
```

### Cobertura dos Testes

Os testes cobrem:
- ✅ Cálculo de desconto percentual/valor ao processar venda
- ✅ Cancelamento de venda com reposição automática de estoque
- ✅ Fechamento esperado do caixa por sessão
- ✅ Agregados de lucratividade (receita, custo, lucro, margem)
- ✅ Validações de formulários
- ✅ Permissões de acesso por grupo

## 📚 Documentação Adicional

- [Documentação do Sistema](docs/documentacao_sistema.md) - Visão geral, instalação e arquitetura
- [Casos de Uso UML](docs/casos_de_uso_uml.md) - Diagramas e fluxos do sistema

## 🔐 Segurança e Boas Práticas

⚠️ **Importante para Produção:**
- Altere a `SECRET_KEY` em `core/settings.py`
- Configure `DEBUG = False`
- Defina `ALLOWED_HOSTS` adequadamente
- Use variáveis de ambiente para credenciais sensíveis
- Configure HTTPS
- Use um servidor WSGI (gunicorn) com nginx

## 🚧 Melhorias Futuras

- [ ] Devolução parcial por item (atualmente só cancelamento total)
- [ ] Exportação de relatórios em CSV e Excel
- [ ] Dashboard com gráficos de vendas e estoque
- [ ] Integração com impressora fiscal
- [ ] API REST para integração com apps mobile
- [ ] Sistema de fidelidade de clientes
- [ ] Nota Fiscal Eletrônica (NF-e)

## 👥 Autor

**João Lucas Cezar**
- GitHub: [@JoaoLCezar](https://github.com/JoaoLCezar)

## 📄 Licença

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC).

---

**Nota**: O fluxo de "Devolução" foi simplificado para "Cancelar Venda" por clareza operacional e escopo do projeto acadêmico.
