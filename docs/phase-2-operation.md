# Fase 2 - Operação do Vendi

## Implementado

- PDV com leitura por código de barras, SKU ou nome, incremento automático e atalhos `F2`, `F4` e `Esc`.
- Carrinho com quantidade inteira ou fracionada conforme a unidade, desconto por item, desconto geral, acréscimo e observação.
- Pagamentos em dinheiro, PIX, débito e crédito, incluindo pagamento misto e cálculo de troco.
- Desconto normal de até 10% para caixa e autorização por credencial de gerente/administrador acima desse limite.
- Venda em espera sem baixa de estoque ou movimentação de caixa, com recuperação e cancelamento pelo próprio operador.
- Finalização transacional com recálculo de preços no backend, validação de estoque, baixa, venda, pagamentos e caixa.
- Cancelamento histórico de venda concluída, com devolução ao estoque, estorno por forma de pagamento e auditoria.
- Abertura, sangria, suprimento e fechamento de caixa com saldo esperado, contagem física e diferença.
- Histórico de caixas com resumo e movimentações; histórico de vendas com filtros, detalhes e comprovante imprimível.
- Proteção contra duplo envio por chave de idempotência e bloqueio do botão enquanto a operação é processada.

## Arquivos

- Backend: `app/models/cash_register.py`, `app/models/sale.py`, `app/services/cash_registers.py`, `app/services/sales.py`, `app/api/routes/cash_registers.py` e `app/api/routes/sales.py`.
- Frontend: `src/pages/CashierPage.tsx`, `src/pages/CashRegistersPage.tsx`, `src/pages/SalesPage.tsx`, `src/services/cashRegisters.ts` e `src/services/sales.ts`.
- Testes: `backend/tests/test_phase2_operations.py` e adaptações de fixture em `backend/tests/conftest.py`.

## Banco

- Novas entidades: `cash_registers`, `cash_movements` e `sale_payments`.
- Venda recebeu vínculo com caixa, acréscimo, observação, chave idempotente e dados de cancelamento.
- A inicialização cria as novas tabelas pelo metadata e atualiza incrementalmente bancos SQLite existentes, preservando o histórico.
- Índice único por estabelecimento e chave idempotente impede vendas duplicadas.

## API

- `GET /cash-registers/current`, `GET /cash-registers` e `GET /cash-registers/{id}`.
- `POST /cash-registers/open`, `POST /cash-registers/withdrawal`, `POST /cash-registers/supply` e `POST /cash-registers/close`.
- `GET /sales` com filtros por status, pagamento, operador e período; `GET /sales/detail/{id}`.
- `POST /sales`, `POST /sales/hold`, `POST /sales/{id}/complete` e `POST /sales/{id}/cancel`.

## Regras

- Uma venda concluída exige caixa aberto e estoque suficiente.
- Unidade `UN` aceita apenas inteiros; unidades por peso aceitam decimais.
- O backend busca os preços atuais, recalcula os totais com `Decimal` e exige que pagamentos somem exatamente o total.
- Dinheiro insuficiente é rejeitado; o excedente recebido vira troco inclusive em pagamento misto.
- Sangria não pode superar o dinheiro esperado disponível.
- Venda concluída nunca é apagada; cancelamento restaura estoque, estorna os meios de pagamento e mantém auditoria.

## Permissões

- Caixa: operar PDV, abrir/fechar o próprio caixa, sangria, suprimento e desconto normal.
- Gerente: visualizar caixas, cancelar venda concluída e autorizar desconto especial.
- Administrador: acesso completo às operações e históricos.
- O backend valida as permissões; esconder ou exibir controles no frontend não é a única proteção.

## Testes

- Cobertura de abertura e segunda abertura, sangria, suprimento, fechamento e diferença.
- Cobertura de venda simples, peso, estoque insuficiente, pagamento misto, soma incorreta e troco.
- Cobertura de espera, recuperação, cancelamento, estoque restaurado, estorno e auditoria.
- Cobertura de desconto especial negado e autorizado.
- Resultado: `28 passed`; frontend compilado com sucesso em `npm run build`.

## Teste manual

1. Entre como administrador e acesse `Caixa`; se necessário, abra com saldo inicial de R$ 100,00.
2. Digite um código, SKU ou nome e pressione Enter; ajuste quantidade e finalize uma venda PIX.
3. Faça outra venda em dinheiro, informe valor recebido maior que o total e confira o troco.
4. Use `Adicionar pagamento`, divida o total entre dinheiro e PIX e confirme.
5. Monte um carrinho, clique em `Colocar em espera`, recupere a venda pela lateral e finalize.
6. Abra `Vendas`, selecione uma venda concluída, imprima o comprovante e cancele informando o motivo.
7. Volte ao caixa, registre um suprimento e uma sangria com motivo.
8. Feche o caixa informando a contagem física e confira esperado e diferença em `Histórico de caixas`.

## Pendências

- NFC-e, adquirentes de cartão e PIX bancário não fazem parte desta fase; os pagamentos são registros operacionais.
- Fiado completo será implementado na Fase 3.
- A sincronização offline permanece planejada para a fase de resiliência.

## Próxima fase

**FASE 3 - Gestão: Fornecedores + Compras + Lotes + Validade + Inventário + Clientes + Fiado.**
