# Fase 1 - Fundação do Vendi

## Implementado

- Produtos persistidos por estabelecimento, com marca, descrição, categoria, fornecedor, SKU, código de barras, custo, venda, estoque mínimo, status e datas.
- Unidades centralizadas em `UN`, `KG`, `G`, `L` e `ML`; produtos `UN` rejeitam quantidades fracionadas.
- SKU e código de barras únicos por estabelecimento, com mensagens amigáveis.
- Margem unitária e margem sobre venda calculadas por regra central usando `Decimal` no backend.
- Busca por nome, SKU ou código de barras e filtros por categoria, situação e estoque baixo.
- Categorias com listagem, criação, edição e exclusão protegida quando existem produtos vinculados.
- Serviço único de estoque para validar, atualizar saldo e registrar histórico com origem opcional.
- Tipos preparados: entrada, saída, ajuste, venda, cancelamento, perda, inventário, compra e devolução.
- Perfis Administrador, Gerente, Caixa e Estoque, permissões centralizadas e proteção no backend.
- Gestão de usuários, inativação segura, alteração de perfil e senhas com hash.
- Auditoria para produtos, categorias, estoque, usuários, perfis/permissões, fornecedores e vendas.

## Banco

Tabelas da fundação: `permissions`, `profiles`, `profile_permissions`, `audit_logs` e `stock_movements`.

Campos incrementais: `users.profile_id`, `products.brand`, `suppliers.active`, `stock_movements.reference_type` e `stock_movements.reference_id`.

A inicialização aplica a migração SQLite sem apagar dados, associa usuários antigos aos perfis e converte unidades legadas para o padrão atual.

## API

- `GET /products`: aceita `search`, `category_id`, `status` e `low_stock`.
- `GET /products/barcode/{code}`: localiza por código de barras, SKU ou nome.
- `POST /products`, `PUT /products/{id}` e `DELETE /products/{id}`: CRUD protegido, validação e inativação segura.
- `GET /categories`, `POST /categories`, `PUT /categories/{id}` e `DELETE /categories/{id}`.
- `POST /inventory/movement` e `GET /inventory/movements`: movimentação e histórico rastreável.
- `GET /profiles` e `PUT /profiles/{id}/permissions`: consulta e alteração auditada de permissões.
- `GET /users`, `POST /users`, `PUT /users/{id}` e `GET /audit`.

## Permissões

- Administrador: acesso completo; permissões do perfil são protegidas contra remoção acidental.
- Gerente: operação, produtos, estoque, fornecedores, vendas, relatórios e auditoria.
- Caixa: somente PDV e consulta operacional de produtos; mutações gerenciais retornam `403`.
- Estoque: produtos, categorias, fornecedores e movimentações, sem administração de usuários.

## Testes

A suíte cobre autenticação, venda, produtos, exclusão/inativação, conflitos de SKU e código de barras, filtros, margem, unidades, estoque, categorias, permissões e auditoria.

Resultado: `19 passed`.

## Teste manual

1. Entre como Administrador e abra `Produtos`.
2. Pesquise por nome ou SKU e teste categoria, situação e estoque baixo.
3. Cadastre um produto e confirme as unidades e a margem sobre venda.
4. Tente repetir o SKU ou código de barras e confira a mensagem amigável.
5. Abra `Categorias`, crie e edite uma categoria; uma categoria vinculada não poderá ser excluída.
6. Altere o estoque de um produto e confira o registro em `Estoque` e `Auditoria`.
7. Em `Equipe`, crie um Caixa e confirme que ações administrativas são bloqueadas.

## Pendências

Nenhuma pendência bloqueante na Fase 1. As advertências de depreciação do Pydantic e do evento de startup foram removidas na Fase 8.

## Próxima fase

**FASE 2 - Operação: PDV + Pagamentos + Caixa + Estoque.**
