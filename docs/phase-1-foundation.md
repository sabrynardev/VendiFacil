# Fase 1 - Fundação do Vendi

## Escopo entregue

- Perfis por estabelecimento: Administrador, Gerente, Caixa e Estoque.
- Permissões centralizadas e verificadas no frontend e no backend.
- Gestão de usuários com criação, edição, ativação, desativação e troca opcional de senha.
- Proteção contra o administrador desativar ou alterar o próprio perfil.
- Auditoria multiempresa para usuários, produtos, estoque, fornecedores e vendas.
- Produto com marca, unidades de medida comerciais e status ativo/inativo.
- Movimentação de estoque criada para estoque inicial e alteração de saldo pelo cadastro.
- Fornecedor com status e arquivamento seguro quando possui produtos vinculados.
- Correção das consultas de lucro e itens vendidos no relatório.

## Banco de dados

Novas tabelas:

- `permissions`
- `profiles`
- `profile_permissions`
- `audit_logs`

Novas colunas:

- `users.profile_id`
- `products.brand`
- `suppliers.active`

A inicialização aplica a migração SQLite de forma incremental e associa usuários existentes aos perfis equivalentes. Dados de contas, produtos e vendas existentes são preservados.

## APIs

- `GET /profiles`: perfis disponíveis para gestão da equipe.
- `GET /users`: usuários da conta atual.
- `POST /users`: cria um usuário na conta atual.
- `PUT /users/{id}`: altera usuário, perfil, status ou senha.
- `GET /audit`: lista até 200 eventos da conta atual e aceita filtro por `entity_type`.
- `GET /auth/me`: agora retorna `profile_name` e `permissions`.

## Regras principais

- Administrador possui todas as permissões.
- Gerente acessa operação e gestão, mas não administra usuários.
- Caixa acessa o PDV e a consulta de produtos necessária à venda.
- Estoque gerencia produtos, fornecedores e movimentações.
- A API valida permissões mesmo quando uma rota é acessada diretamente.
- Registros de auditoria nunca são misturados entre estabelecimentos.

## Teste manual

1. Entre como Administrador e abra `Equipe` na barra lateral.
2. Cadastre um usuário Caixa e confirme que ele aparece como ativo.
3. Saia, entre com o novo Caixa e confirme que somente o PDV aparece.
4. Entre novamente como Administrador e edite um produto, preenchendo a marca.
5. Abra `Auditoria` e confirme os eventos de criação do usuário e alteração do produto.
6. Abra `Relatórios` e alterne os períodos para validar os indicadores.

## Próxima etapa

A Fase 2 deve evoluir PDV, pagamentos, abertura e fechamento de caixa, vendas em espera e cancelamento com estorno de estoque, usando as permissões e a auditoria entregues aqui.
