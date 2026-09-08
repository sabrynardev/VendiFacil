# VendiFácil

Sistema completo de PDV para mercadinho com frontend em React + TypeScript e backend em FastAPI, pensado para demonstração profissional e evolução real do produto.

![VendiFácil Cover](docs/repo-cover.svg)

## Destaques

- Fluxo de venda funcional de ponta a ponta com autenticação, carrinho, pagamento simulado, baixa de estoque e histórico
- Dashboard com indicadores operacionais, alertas de ruptura e visual pronto para demonstração
- Backend organizado em camadas com FastAPI, SQLAlchemy, Pydantic, JWT e testes automatizados
- Frontend moderno com dark mode, navegação responsiva e páginas preparadas para portfólio
- Estrutura clara para evolução futura com PostgreSQL, relatórios, previsão de estoque e múltiplos perfis

## Demo rápida

1. Faça login com `admin@marketpulse.dev` e `admin123`
2. Abra `Produtos` para visualizar o catálogo seedado
3. Vá para `Caixa` e pesquise por um item via nome, SKU ou código de barras
4. Adicione duas unidades ao carrinho
5. Finalize a venda com `PIX`
6. Valide o reflexo da operação em `Vendas`, `Estoque` e `Dashboard`

## Página de apresentação comercial

Além da área autenticada, o projeto agora possui uma rota pública para demonstração comercial:

- [http://localhost:5173/apresentacao](http://localhost:5173/apresentacao)

Essa página foi pensada para:

- captar clientes locais
- apresentar os benefícios do sistema sem login
- mostrar planos sugeridos de implantação e suporte
- servir como base para anúncios, WhatsApp e reuniões presenciais

## Por que este projeto é forte para portfólio

- Resolve um problema real de operação comercial, em vez de ser apenas um CRUD genérico
- Mostra integração entre frontend, backend, autenticação, banco de dados e regras de negócio
- Demonstra cuidado com UX, arquitetura e consistência visual
- Inclui validação automatizada do fluxo crítico de negócio

## Visão geral

O VendiFácil foi estruturado como um monorepo com:

- `frontend/`: interface responsiva com dark mode, sidebar, dashboard, PDV, produtos, estoque, vendas, fornecedores e relatórios.
- `backend/`: API REST com autenticação JWT, regras de venda transacional, seed inicial, estoque, dashboard e relatórios.
- `docker-compose.yml`: PostgreSQL opcional para rodar localmente.

## Funcionalidades implementadas

- Login com JWT e proteção de rotas
- Perfis `ADMIN`, `CAIXA` e `ESTOQUE`
- Dashboard com:
  - faturamento diário
  - vendas do dia
  - ticket médio
  - alertas de estoque
  - gráfico de faturamento
  - vendas por categoria
  - formas de pagamento
  - ranking de produtos
- PDV com:
  - busca por código de barras, SKU ou nome
  - carrinho com ajuste de quantidade
  - desconto por item e desconto geral
  - modal de finalização
  - pagamento por PIX, dinheiro, débito e crédito
  - atalho `F2`, `F4`, `ESC` e `Delete`
- CRUD de produtos
- CRUD de fornecedores
- Tela de estoque com:
  - status automático
  - previsão de ruptura
  - sugestão de reposição para 15 dias
  - movimentações recentes
- Histórico de vendas com detalhamento
- Relatórios resumidos por período
- Seed com categorias, fornecedores, produtos e vendas históricas
- Migração inicial com Alembic

## Arquitetura

```text
vendifacil/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── main.py
│   │   └── seed.py
│   ├── requirements.txt
│   └── smoke_test.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
├── .env.example
├── docker-compose.yml
└── README.md
```

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React
- Backend: FastAPI, SQLAlchemy, Pydantic
- Auth: JWT
- Banco: PostgreSQL
- Migração: Alembic

## Como instalar

### 1. Banco de dados

Opção com Docker:

```bash
docker compose up -d
```

Banco esperado:

- host: `localhost`
- porta: `5432`
- database: `vendifacil`
- user: `postgres`
- password: `postgres`

### 2. Variáveis de ambiente

Na raiz do projeto:

```bash
cp .env.example backend/.env
cp frontend/.env.example frontend/.env
```

Se estiver no Windows PowerShell:

```powershell
Copy-Item .env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

O arquivo [backend/.env.example](/F:/pdv/backend/.env.example) já vem pronto para PostgreSQL local com Docker.

### 3. Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

No Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Para rodar os testes do backend:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Comandos principais

Backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

Build do frontend:

```bash
cd frontend
npm run build
```

Smoke test do fluxo principal:

```bash
cd backend
python smoke_test.py
```

## Usuários padrão

- Admin: `admin@marketpulse.dev` / `admin123`
- Caixa: `sabrina@marketpulse.dev` / `caixa123`

## Endpoints principais

### Auth

- `POST /auth/login`
- `GET /auth/me`

### Products

- `GET /products`
- `GET /products/{id}`
- `GET /products/barcode/{barcode}`
- `POST /products`
- `PUT /products/{id}`
- `DELETE /products/{id}`

### Sales

- `GET /sales`
- `GET /sales/{id}`
- `POST /sales`

### Inventory

- `GET /inventory`
- `GET /inventory/alerts`
- `GET /inventory/predictions`
- `GET /inventory/movements`
- `POST /inventory/movement`

### Suppliers

- `GET /suppliers`
- `POST /suppliers`
- `PUT /suppliers/{id}`
- `DELETE /suppliers/{id}`

### Dashboard

- `GET /dashboard/summary`
- `GET /dashboard/revenue`
- `GET /dashboard/top-products`
- `GET /dashboard/payment-methods`
- `GET /dashboard/category-sales`

### Reports

- `GET /reports?period=today|7d|30d`

## Como cada parte funciona

- `Auth`: login gera JWT e o frontend persiste o token no `localStorage`.
- `PDV`: busca o produto, adiciona ao carrinho e envia a venda para a API.
- `Venda`: o backend valida estoque, cria venda e itens, reduz saldo e registra movimentação.
- `Estoque`: calcula status, média diária, previsão de ruptura e recomendação de compra.
- `Dashboard`: agrega vendas históricas para cards e gráficos.

## PostgreSQL em definitivo

Para usar PostgreSQL como base principal do projeto:

1. Suba o banco com `docker compose up -d` na raiz.
2. Copie `backend/.env.example` para `backend/.env`.
3. Confirme que `DATABASE_URL` aponta para `postgresql+psycopg://postgres:postgres@localhost:5432/marketpulse`.
4. Rode `alembic upgrade head`.
5. Inicie o backend.

Observação:

- O backend ainda aceita SQLite para testes e validações rápidas.
- Em ambiente de demonstração mais sério, prefira PostgreSQL.

## Testes automatizados

Foram adicionados testes em [backend/tests](/F:/pdv/backend/tests):

- autenticação com sucesso e falha
- busca de produto por código de barras
- venda com baixa automática de estoque
- registro de movimentação
- cálculo de troco em dinheiro
- bloqueio de venda sem estoque suficiente

Execução:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Validação executada

Execuções realizadas nesta entrega:

- `python -m compileall backend/app`
- `python -c "from fastapi.testclient import TestClient; ... /health ..."`
- `python smoke_test.py`
- `npm run build`

O smoke test confirmou:

- login
- listagem de produtos
- busca por código de barras
- venda com duas unidades
- baixa automática de estoque
- registro de movimentação
- atualização do dashboard
- presença da venda no histórico

## Screenshots

### Dashboard

![Dashboard](docs/screenshots/dashboard.png)

### Produtos

![Produtos](docs/screenshots/products.png)

### Estoque

![Estoque](docs/screenshots/inventory.png)

### Caixa

![Caixa](docs/screenshots/cashier.png)

### Finalização de venda

![Checkout](docs/screenshots/checkout-modal.png)

### Histórico de vendas

![Vendas](docs/screenshots/sales.png)

Sugestão de sequência para capturas:

- Login
- Dashboard
- Caixa com carrinho preenchido
- Histórico de vendas
- Estoque com alertas e previsão

## Roadmap

### V1

- autenticação
- produtos
- caixa
- vendas
- estoque

### V2

- fornecedores
- dashboard
- relatórios

### V3

- previsão de estoque
- sugestão de compras

### V4

- emissão NFC-e
- integração PIX real
- multi-loja
- múltiplos caixas
- leitor de balança
- integração ERP
- aplicativo mobile
- fidelidade
- relatórios avançados
- inteligência artificial

## Observações

- NFC-e e pagamentos reais não foram implementados nesta versão.
- O projeto está pronto para rodar com PostgreSQL, mas o smoke test local foi executado com SQLite isolado para validação rápida do fluxo sem afetar a base principal.
