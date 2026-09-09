# Vendi - Fase 5: Analytics

## Implementado

- Dashboard gerencial com faturamento, CMV histórico, lucro bruto, resultado estimado, vendas, ticket médio e comparação com o período anterior.
- Filtro global por hoje, ontem, 7/30 dias, mês atual/anterior, ano e período personalizado.
- Relatórios de vendas por dia, horário e forma de pagamento, inclusive pagamentos mistos.
- Desempenho de produtos e categorias por quantidade, faturamento, CMV, lucro absoluto, margem e participação.
- Curva ABC por faturamento líquido, com percentual individual, acumulado e explicação das classes.
- Estoque valorizado a custo e preço de venda, giro simplificado, estoque baixo, cobertura, possível excesso e produtos parados em 15/30/60/90 dias.
- Clientes por faturamento e ticket médio; fiado por saldo, atraso, idade, faixas e maiores devedores.
- Fornecedores por compras recebidas, concentração, frequência, evolução de custos e comparação por produto.
- Perdas por motivo e produto, custo congelado na baixa, impacto sobre lucro bruto e valor em risco por validade.
- Exportação CSV de produtos, Curva ABC, produtos parados, fornecedores e perdas.
- Dashboard operacional preservado para usuários sem permissão de Analytics.

## Banco

- `inventory_losses.unit_cost`: snapshot do custo na data da perda, com backfill seguro para bases existentes.
- Índices para consultas por conta, período, status, produto, cliente, dívida, perda, preço de fornecedor e pagamento.
- Não há tabelas analíticas duplicadas: os indicadores são derivados dos dados operacionais reais.

## API

- `GET /api/analytics/overview?start=YYYY-MM-DD&end=YYYY-MM-DD&stopped_days=30`
- `GET /api/analytics/export?report=products|abc|stopped|suppliers|losses&start=YYYY-MM-DD&end=YYYY-MM-DD`

## Regras

- Vendas canceladas e em espera não entram em faturamento.
- O CMV usa o custo congelado no item vendido, portanto alterações futuras de custo não mudam o passado.
- Descontos e acréscimos da venda são distribuídos proporcionalmente entre os itens.
- A Curva ABC é ordenada por faturamento e classificada pelo acumulado: A até 80%, B até 95% e C no restante.
- Produto parado precisa possuir estoque e não ter venda além do limite selecionado; produto novo respeita a própria data de cadastro.
- Giro simplificado = CMV do período / estoque atual valorizado a custo.
- Saldo de fiado considera apenas débitos ainda abertos; dívidas pagas não entram nos rankings.
- Perdas usam o custo do lote quando disponível ou o custo do produto no momento da baixa.
- Valores gerenciais são estimativas operacionais e não substituem demonstrações contábeis oficiais.

## Permissões

- Administrador recebe todas as permissões de Analytics e relatórios.
- Gerente pode visualizar Analytics e relatórios de vendas, estoque, financeiro, clientes e fornecedores, além de exportar CSV.
- Caixa mantém o dashboard operacional e não recebe acesso a lucro, CMV ou relatórios gerenciais.

## Testes

O arquivo `backend/tests/test_phase5_analytics.py` cobre Curva ABC, períodos vazios, CMV histórico, pagamentos mistos, produtos parados, fiado, perdas com custo congelado, fornecedores e CSV.

Validação recomendada:

```powershell
backend\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```

## Teste manual

1. Entre como administrador ou gerente e abra o Dashboard.
2. Troque o período e confira a comparação com o período anterior.
3. Acesse Relatórios e percorra as abas Visão geral, Produtos, Curva ABC, Estoque, Clientes, Fornecedores e Perdas.
4. Confirme que um período sem movimento exibe estados vazios, sem números inventados.
5. Na aba Estoque, altere o limite de produtos parados entre 15, 30, 60 e 90 dias.
6. Exporte um CSV e abra o arquivo verificando o mesmo período selecionado.
7. Entre como caixa e confirme que indicadores de lucro permanecem ocultos.

## Pendências

- Paginação server-side para relatórios com milhares de registros.
- Relatório detalhado de movimentações de estoque com filtros próprios.
- Exportação em PDF e impressão formatada; nesta fase a exportação é CSV.
- Indicadores avançados de reposição e recomendações pertencem à Fase 6.

## Próxima fase

**Fase 6 - Inteligência: previsão de reposição, Vendi Inteligente e Pergunte ao Vendi.**
