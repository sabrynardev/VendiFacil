# Fase 3 - Gestão do Vendi

## Implementado

- Fornecedores ampliados com nome fantasia, cidade, UF, atualização e inativação segura.
- Relação de vários fornecedores por produto com código externo, último custo, última compra, preferência e prazo de entrega.
- Pedidos de compra com itens, totais calculados no backend, status centralizados, cancelamento e recebimento parcial ou total.
- Recebimento transacional com entrada automática no estoque, movimentação `COMPRA`, atualização de custo, lote opcional e histórico imutável de preços.
- Comparação de custos por produto/fornecedor e cálculo de variação percentual em relação ao preço anterior.
- Lotes com saldo, custo, origem, validade e estados dinâmicos de vencimento.
- Perdas por vencimento, dano, quebra, consumo interno, furto ou outro motivo, atualizando lote e estoque na mesma transação.
- Inventários totais ou por categoria, contagem física, diferenças positivas/negativas, ajuste de estoque, cancelamento e histórico.
- Clientes com cadastro rápido, limite de crédito opcional, bloqueio de fiado e indicadores de compras.
- Venda fiada ou mista no PDV, cliente obrigatório, vencimento opcional, limite e autorização gerencial para excesso.
- Dívidas independentes por venda, pagamentos parciais/totais e alocação FIFO nas dívidas mais antigas.
- Recebimento de fiado no caixa sem criar nova venda, histórico, comprovante e alertas de atraso.
- Cancelamento de venda fiada restaura estoque e estorna o débito sem apagar o histórico.

## Arquivos

- Modelos: `app/models/purchase.py`, `app/models/management_inventory.py` e `app/models/customer.py`.
- Serviços: `app/services/purchases.py`, `app/services/management_inventory.py` e `app/services/customers.py`.
- Rotas: `app/api/routes/purchases.py`, `app/api/routes/management_inventory.py` e `app/api/routes/customers.py`.
- Frontend: `PurchasesPage.tsx`, `LotsPage.tsx`, `InventoryCountsPage.tsx`, `CustomersPage.tsx` e evolução do `CashierPage.tsx`.
- Testes: `backend/tests/test_phase3_management.py`.

## Banco

- Compras: `product_suppliers`, `purchase_orders`, `purchase_order_items`, `purchase_receipts`, `purchase_receipt_items` e `supplier_price_history`.
- Estoque: `product_lots`, `inventory_losses`, `inventory_counts` e `inventory_count_items`.
- Clientes: `customers`, `customer_debts`, `customer_payments` e `customer_payment_allocations`.
- Campos incrementais em fornecedor e venda preservam registros antigos.
- A inicialização cria novas tabelas pelo metadata e aplica migração incremental segura no SQLite atual, sem apagar dados.

## API

- Compras: `GET/POST /purchases`, `GET /purchases/{id}`, `POST /purchases/{id}/receive`, `POST /purchases/{id}/cancel` e `GET /purchases/history/prices`.
- Fornecedor/produto: `GET/POST /purchases/suppliers/{id}/products`.
- Lotes e perdas: `GET/POST /management-inventory/lots`, `GET /management-inventory/expiry-alerts` e `GET/POST /management-inventory/losses`.
- Inventários: `GET/POST /management-inventory/counts`, `POST /management-inventory/counts/{id}/complete` e `POST /management-inventory/counts/{id}/cancel`.
- Clientes: `GET/POST /customers`, `GET/PUT /customers/{id}` e `POST /customers/{id}/payments`.
- Vendas: `POST /sales` agora aceita `customer_id`, `credit_due_date` e pagamento `FIADO`.

## Regras

- Quantidades recebidas não podem superar o pendente e cada confirmação é atômica com o estoque.
- Histórico de preços nunca é sobrescrito; a variação usa o preço anterior do mesmo produto e fornecedor.
- Validade é calculada dinamicamente em vencido, hoje, 3, 7, 30 dias ou normal.
- Perda com lote valida produto e saldo; a movimentação de estoque aponta para a perda.
- Inventário só altera estoque ao concluir; cancelamento não movimenta nada.
- Limite nulo significa sem limite definido; cliente bloqueado não compra fiado.
- Pagamentos de fiado não podem superar o saldo e abatem primeiro as dívidas mais antigas.
- Recebimento durante caixa aberto gera `RECEBIMENTO_FIADO`, separado de faturamento.

## Permissões

- Administrador: acesso completo.
- Gerente: fornecedores, compras, recebimentos, lotes, perdas, inventários, clientes, limites, fiado e autorizações.
- Caixa: consulta de clientes, venda fiada dentro do limite e recebimento de fiado.
- Estoque: fornecedores, compras, recebimentos, lotes, perdas e inventários, sem gestão de crédito.

## Testes

- Compra, total, vínculo, recebimento parcial/completo, excesso inválido, estoque, lote, preço e variação.
- Lote vencido, perda, saldo do lote e movimentação.
- Inventário positivo, negativo, conclusão e cancelamento sem alteração.
- Cliente obrigatório, venda fiada, múltiplas dívidas, FIFO, pagamentos parcial/total, limite, autorização, atraso, bloqueio e cancelamento.
- Resultado final: `34 passed`; frontend compilado com sucesso em `npm run build`.

## Teste manual

1. Em `Fornecedores`, cadastre ou edite um fornecedor e use o ícone de vínculo para adicionar produtos.
2. Em `Compras`, crie um pedido escolhendo fornecedor, produtos, quantidades e custos.
3. Clique em `Receber`, informe apenas parte da quantidade e confirme o status `PARCIALMENTE_RECEBIDO`.
4. No recebimento, informe lote e validade; confira em `Lotes e validade`.
5. No lote, clique em `Registrar perda`, escolha motivo e confirme a baixa no estoque.
6. Em `Inventários`, inicie uma categoria, informe as quantidades físicas e conclua.
7. Em `Clientes e fiado`, cadastre Maria com limite de crédito.
8. No `Caixa`, selecione Maria, adicione itens, escolha `FIADO`, vencimento e finalize.
9. Volte ao cliente, clique em `Receber`, informe parte do saldo e confira dívida parcial e comprovante.
10. Edite ou abra o cliente para bloquear fiado; no PDV a nova venda fiada ficará impedida.

## Pendências

- A saída automática de saldo dos lotes no PDV por FEFO está preparada pela ordenação de validade, mas será integrada quando a operação de venda por lote for habilitada.
- O SQLite local é migrado automaticamente. Uma consolidação futura do histórico Alembic legado será necessária antes de atualizar instalações PostgreSQL criadas apenas pela migration `0001_initial`.

## Próxima fase

**FASE 4 - Financeiro: Receitas + Despesas + Contas a Pagar/Receber + Fluxo de Caixa + Fechamento Gerencial.**
