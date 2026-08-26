# Demo Script

## Duração sugerida

5 a 8 minutos

## Abertura

“Este é o VendiFácil, um sistema de PDV pensado para pequenos mercados e lojas de conveniência. A proposta foi construir um produto visualmente profissional e funcional, com fluxo real de venda, controle de estoque e visão gerencial.”

## Roteiro

### 1. Login

- mostrar a tela de autenticação
- entrar com o usuário administrador
- destacar autenticação via JWT

### 2. Dashboard

- mostrar faturamento do dia
- destacar ticket médio, alertas e gráficos
- explicar que os dados são abastecidos pelas vendas seedadas e pelas novas vendas realizadas

### 3. Produtos

- abrir a tela de produtos
- mostrar SKU, código de barras, margem e status de estoque
- destacar organização do cadastro

### 4. Caixa

- abrir a tela de caixa
- pesquisar um produto por nome ou código
- adicionar duas unidades
- comentar sobre atalhos e foco automático no campo principal

### 5. Finalização

- abrir o modal de checkout
- escolher `PIX`
- confirmar a venda
- explicar que a API valida estoque antes de concluir

### 6. Pós-venda

- abrir `Vendas` para mostrar o registro
- abrir `Estoque` para mostrar a baixa automática
- abrir `Dashboard` para mostrar o reflexo nos indicadores

## Fechamento

“Além da interface, o projeto também foi estruturado com backend em camadas, autenticação, testes automatizados do fluxo crítico e preparação para PostgreSQL, o que torna essa base evoluível para cenários mais reais.”
