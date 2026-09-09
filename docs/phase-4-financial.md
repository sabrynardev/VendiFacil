# Vendi - Fase 4: Financeiro

## Implementado

- Dashboard financeiro por período, com atalhos para hoje e mês atual.
- Faturamento, recebimentos, CMV, lucro bruto, margem bruta, despesas operacionais e resultado estimado.
- Separação entre faturamento, venda fiada, recebimento de fiado e entrada financeira.
- Snapshot do custo do produto em cada item de venda para preservar o histórico.
- Categorias financeiras configuráveis com categorias iniciais por conta.
- Contas a pagar manuais ou vinculadas a pedidos de compra.
- Pagamentos parciais e totais, histórico de pagamentos e proteção por idempotência.
- Pagamento opcional em dinheiro pelo caixa físico, gerando uma única retirada operacional.
- Contas a receber consolidadas com o fiado, sem duplicar a dívida do cliente.
- Recebíveis manuais e recebimentos parciais pela API.
- Receitas manuais sem duplicar o faturamento de vendas.
- Despesas recorrentes semanais, mensais e anuais, com geração protegida por período.
- Fluxo de caixa consolidado por vendas recebidas, fiado recebido, receitas, recebíveis e pagamentos.
- Projeção de compromissos reais para os próximos 7 e 30 dias.
- Conciliação operacional básica para vendas sem pagamento, fiado sem alocação, diferenças de caixa e compras recebidas sem obrigação.
- Auditoria para criação, alteração, pagamento, cancelamento e geração financeira.

## Arquivos principais

- `backend/app/models/financial.py`
- `backend/app/schemas/financial.py`
- `backend/app/services/financial.py`
- `backend/app/api/routes/financial.py`
- `backend/tests/test_phase4_financial.py`
- `frontend/src/pages/FinancialPage.tsx`
- `frontend/src/services/financial.ts`

## Banco

Novas tabelas:

- `financial_categories`
- `payables`
- `payable_payments`
- `manual_revenues`
- `financial_receivables`
- `receivable_receipts`
- `recurring_expenses`

O campo `sale_items.cost_price` congela o custo usado na venda. Instalações SQLite existentes recebem o campo automaticamente no bootstrap e têm os registros antigos preenchidos com o custo atual disponível no momento da migração. Instalações novas armazenam o custo correto desde a venda.

## API

- `GET/POST /financial/categories`
- `GET/POST /financial/payables`
- `PUT /financial/payables/{id}`
- `POST /financial/payables/{id}/payments`
- `POST /financial/payables/{id}/cancel`
- `GET/POST /financial/revenues`
- `POST /financial/revenues/{id}/cancel`
- `GET/POST /financial/receivables`
- `POST /financial/receivables/{id}/receipts`
- `GET/POST /financial/recurring`
- `POST /financial/recurring/generate`
- `GET /financial/summary`
- `GET /financial/cash-flow`
- `GET /financial/projections`
- `GET /financial/reconciliation`

## Regras financeiras

- Faturamento soma somente vendas concluídas; vendas canceladas ficam fora.
- Venda fiada compõe faturamento, mas não recebimento imediato.
- Pagamento de fiado compõe entrada financeira, mas não cria novo faturamento.
- CMV usa quantidade vendida multiplicada pelo custo congelado no item da venda.
- Lucro bruto é faturamento menos CMV.
- Resultado estimado é lucro bruto menos pagamentos de despesas marcadas como operacionais.
- Pagamentos de fornecedores entram no fluxo de caixa, mas compras para estoque não são subtraídas novamente do resultado que já usa CMV.
- O módulo financeiro é consolidado e permanece separado das sessões do caixa do PDV.

## Permissões

- Administrador: acesso completo.
- Gerente: visualização financeira, custos, lucro, despesas, receitas, pagamentos e contas.
- Caixa e Estoque: sem acesso ao módulo financeiro por padrão.
- Todas as rotas validam permissões no backend.

## Testes

- 6 novos testes financeiros.
- 40 testes totais executados com sucesso.
- Cobertura funcional de pagamentos parciais/totais, idempotência, vencimento, cancelamento, caixa físico, compra, recorrência, recebíveis, fluxo, CMV e fiado.
- Cenário obrigatório validado: R$ 200 de faturamento, R$ 100 recebidos, CMV de R$ 110, lucro bruto de R$ 90, despesa de R$ 20 e resultado de R$ 70. O recebimento posterior do fiado altera o caixa, mas mantém o faturamento em R$ 200.

## Teste manual

1. Entre como administrador e abra `Financeiro` na barra lateral.
2. Clique em `Nova despesa`, informe categoria, valor e vencimento.
3. Abra `Contas a pagar`, clique em `Pagar` e registre apenas parte do saldo.
4. Repita o pagamento com o saldo restante e confirme o status `PAGA`.
5. No PDV, realize uma venda em dinheiro.
6. Cadastre um cliente e realize outra venda em `FIADO`.
7. Em `Clientes e fiado`, receba a dívida do cliente.
8. Volte ao Financeiro e compare `Faturamento` com `Recebimentos`.
9. Confira as abas `Fluxo de caixa`, `Contas a receber` e `Recorrentes`.
10. Use os filtros `Hoje` e `Este mês` para validar o fechamento gerencial.

## Pendências reais

- Estorno financeiro dedicado para pagamentos já realizados. Por segurança, contas pagas não podem ser canceladas diretamente.
- Geração automática de parcelas de uma compra; hoje cada parcela pode ser cadastrada como uma conta independente.
- Gestão de contas bancárias, conciliação bancária e saldos por banco. A visão atual é operacional consolidada.
- Consolidação da cadeia antiga de migrations Alembic/PostgreSQL antes de implantação baseada apenas nas migrations; SQLite é atualizado automaticamente.

## Próxima fase

FASE 5 - Analytics: Dashboard avançado, Relatórios, Curva ABC, Produtos Parados, Margens e Análise de Fornecedores.
