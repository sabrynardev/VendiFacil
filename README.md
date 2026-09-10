# VendiFácil Pro

PDV e gestão para mercadinhos e pequenos varejos, desenvolvido com React, TypeScript, FastAPI e SQLAlchemy. O sistema reúne operação de caixa, estoque, compras, clientes, fiado, financeiro, analytics, recomendações determinísticas e contingência offline.

![VendiFácil Pro](docs/repo-cover.svg)

## Estado atual

O projeto é uma demonstração funcional avançada e um piloto local viável. Os fluxos críticos possuem persistência e regras no backend; não são telas mockadas. Ainda não deve ser tratado como SaaS público ou solução fiscal pronta sem concluir os itens descritos em [Produção](#produção).

Funciona hoje:

- contas isoladas por estabelecimento, login JWT, perfis e permissões;
- produtos, categorias, fornecedores, compras, recebimentos e histórico de preços;
- PDV, caixa, pagamento misto, troco, venda em espera, cancelamento e comprovante não fiscal;
- estoque transacional, lotes, validade, perdas e inventários;
- clientes, limite de crédito, fiado e pagamentos parciais;
- receitas, despesas, contas, recorrências, fluxo de caixa e indicadores gerenciais;
- relatórios, Curva ABC, produtos parados, margens e exportação CSV;
- Vendi Inteligente e Pergunte ao Vendi com consultas determinísticas aos dados reais;
- fila offline de vendas com idempotência, conflito auditável e sincronização;
- auditoria das operações sensíveis.

## Screenshots

| Dashboard | Produtos |
|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Produtos](docs/screenshots/products.png) |

| Estoque | Caixa |
|---|---|
| ![Estoque](docs/screenshots/inventory.png) | ![Caixa](docs/screenshots/cashier.png) |

| Finalização | Histórico de vendas |
|---|---|
| ![Finalização](docs/screenshots/checkout-modal.png) | ![Vendas](docs/screenshots/sales.png) |

## Stack e arquitetura

- Frontend: React 19, TypeScript, Vite, Tailwind CSS, Recharts e IndexedDB.
- Backend: FastAPI, Pydantic, SQLAlchemy e JWT.
- Banco: PostgreSQL recomendado; SQLite suportado para desenvolvimento e testes.
- Migração: Alembic com baseline completo do esquema atual.
- Estrutura: rotas finas, serviços de negócio, modelos, schemas e componentes reutilizáveis.

```text
frontend/src/       páginas, componentes, contextos, serviços e tipos
backend/app/api/    endpoints e autorização
backend/app/services regras de negócio e transações
backend/app/models/ entidades SQLAlchemy
backend/tests/      testes de integração e regras críticas
docs/               documentação por fase, auditoria e material comercial
```

## Instalação local

Pré-requisitos: Python 3.11+, Node.js 20+ e, para PostgreSQL, Docker Desktop ou uma instância compatível.

### 1. Configuração

No PowerShell, na raiz do projeto:

```powershell
Copy-Item .env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Para usar PostgreSQL local:

```powershell
docker compose up -d
```

O `docker-compose.yml` cria o banco `vendifacil` em `localhost:5432`.

### 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API: `http://127.0.0.1:8000`

Swagger: `http://127.0.0.1:8000/docs`

Saúde: `http://127.0.0.1:8000/health`

### 3. Frontend

Em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Aplicação: `http://localhost:5173`

## Demonstração

Com `APP_ENVIRONMENT=development` e `AUTO_SEED=true`, o seed local cria dados realistas e usuários de demonstração definidos pelas variáveis `SEED_ADMIN_EMAIL` e `SEED_ADMIN_PASSWORD`. O operador demonstrativo é criado somente nesse seed. Nunca use essas credenciais ou mantenha o seed ativo em produção.

Roteiro sugerido:

1. Entre com o administrador configurado no ambiente.
2. Abra um caixa e informe o saldo inicial.
3. Busque um produto por nome, SKU ou código de barras.
4. Finalize uma venda com dinheiro, PIX, cartão ou pagamento misto.
5. Confira venda, caixa, estoque, dashboard e auditoria.
6. Explore compras, clientes, financeiro, relatórios e Vendi Inteligente.
7. Acesse `http://localhost:5173/apresentacao` para a página comercial pública.

## Validação

```powershell
cd backend
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pip check

cd ..\frontend
npm run build
npm audit --omit=dev --audit-level=high
```

A auditoria da Fase 8 executou 58 testes, compilou o frontend e validou uma criação limpa das 38 tabelas via Alembic. Consulte [docs/phase-8-final-audit.md](docs/phase-8-final-audit.md).

## Configuração de produção

Defina pelo menos:

```env
APP_ENVIRONMENT=production
AUTO_SEED=false
JWT_SECRET_KEY=uma-chave-aleatoria-com-32-ou-mais-caracteres
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/vendifacil
BACKEND_CORS_ORIGINS=https://seu-dominio.example
BUSINESS_TIMEZONE=America/Bahia
```

O backend recusa a inicialização em produção quando a chave JWT é fraca ou o seed está ativo.

## Produção

Antes de uso comercial amplo, ainda são necessários:

- HTTPS, domínio, proxy reverso e deploy com monitoramento;
- backups automáticos externos e teste periódico de restauração;
- migração assistida para bancos PostgreSQL criados por versões antigas do projeto;
- armazenamento de sessão mais resistente a XSS, revogação/rotação de tokens e recuperação de senha;
- rate limiting compartilhado entre instâncias e proteção adicional no cadastro público;
- observabilidade centralizada, alertas, política de retenção e tratamento de dados pessoais;
- testes E2E de navegador, carga, concorrência real e validação em dispositivos de caixa;
- estratégia de reconciliação operacional para conflitos offline e limpeza segura do dispositivo;
- integração fiscal, TEF/PIX bancário e homologações, caso o produto passe a emitir documentos ou processar pagamentos.

O comprovante atual é interno e não possui validade fiscal. O financeiro é gerencial e não substitui escrituração contábil.

## Documentação

- [Auditoria final e prontidão](docs/phase-8-final-audit.md)
- [Fase 1: Fundação](docs/phase-1-foundation.md)
- [Fase 2: Operação](docs/phase-2-operation.md)
- [Fase 3: Gestão](docs/phase-3-management.md)
- [Fase 4: Financeiro](docs/phase-4-financial.md)
- [Fase 5: Analytics](docs/phase-5-analytics.md)
- [Fase 6: Inteligência](docs/phase-6-intelligence.md)
- [Fase 7: Resiliência](docs/phase-7-resilience.md)
- [Roteiro de demonstração](docs/demo-script.md)
- [Playbook de venda local](docs/local-sales-playbook.md)
- [Estudo de caso para portfólio](docs/portfolio-case-study.md)

## Licença e suporte

O repositório não possui licença pública definida. Contato comercial: Sabryna R DEV, `sabrynxr@gmail.com`, `(75) 98883-4910`.
