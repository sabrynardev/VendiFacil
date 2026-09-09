# Vendi - Fase 6: Inteligência

## Implementado

- Previsão de cobertura e ruptura baseada nas vendas reais dos últimos 30 dias.
- Ponto de pedido, estoque de segurança e sugestão revisável de quantidade de compra.
- Central Vendi Inteligente com filtros, prioridades, ações de navegação e explicação de cada cálculo.
- Insights de estoque baixo, ruptura, reposição, excesso, produto parado, margem baixa, custo crescente, perdas, validade, fiado, faturamento e sazonalidade simples.
- Comparação com período anterior e produtos que mais contribuíram para quedas de faturamento.
- Pergunte ao Vendi com interpretação de períodos, perguntas sugeridas, histórico da sessão e fontes da resposta.
- Operação integral sem LLM: cálculos e respostas principais são determinísticos e usam somente dados internos.

## Banco e configuração

- Nova tabela `assistant_query_logs`, com conta, usuário, intenção, ferramenta, sucesso, duração e data. A pergunta não é armazenada.
- Índice `ix_assistant_query_account_period` para observabilidade por conta e período.
- Variáveis em `backend/.env.example`: janela padrão, dias de segurança, horizonte de compra, limite de aumento de custo, dias sem venda, habilitação do assistente e provider.
- Nenhuma chave real foi incluída. `AI_PROVIDER=disabled` mantém o fallback local ativo.

## Motor de insights

`app.services.intelligence` consome os serviços da Fase 5 e segue o fluxo dado real, cálculo determinístico, insight e explicação. Os IDs são estáveis por tipo e entidade, evitando duplicações. Como os insights são calculados sob demanda, deixam de aparecer automaticamente quando estoque, venda, compra, perda ou pagamento muda.

Prioridades objetivas:

- `CRITICO`: estoque zerado, cobertura de até 3 dias ou validade em até 3 dias.
- `IMPORTANTE`: estoque baixo, cobertura de até 7 dias, reposição, margem muito baixa ou fiado vencido.
- `ATENCAO`: excesso, produto parado, custo subindo, perdas e queda de faturamento.
- `INFORMATIVO`: crescimento e padrões de demanda com amostra suficiente.

## Previsão

- Janela padrão: 30 dias corridos, incluindo dias sem venda.
- Histórico mínimo: duas vendas concluídas na janela. Abaixo disso, o sistema informa que não há base suficiente.
- Média diária: quantidade vendida / dias da janela.
- Cobertura: estoque atual / média diária.
- Estoque de segurança: maior valor entre estoque mínimo e demanda dos dias de segurança configurados.
- Ponto de pedido: demanda diária x prazo do fornecedor + estoque de segurança.
- Sugestão: demanda durante prazo + 7 dias de revisão + segurança - estoque atual.
- Sem lead time cadastrado, o Vendi não inventa ponto de pedido ou quantidade; solicita revisão do prazo.
- A sugestão apenas navega para Compras. Nenhum pedido é confirmado automaticamente.

## Pergunte ao Vendi

- Provider atual: `deterministic-local`; a abstração `AIProvider` está preparada para integração futura.
- Ferramentas fechadas: resumo de vendas, margens, produtos, risco de estoque, fiado, fornecedores e perdas.
- Períodos: hoje, ontem, esta semana, semana passada, este mês, mês passado, últimos N dias ou filtro da tela.
- O perfil Caixa pode abrir o assistente, mas lucro e demais dados sem permissão são bloqueados antes da consulta.
- Quando não há dados, a resposta declara a ausência em vez de estimar valores.

## Segurança

- Endpoints autenticados e isolados por `account_id`.
- Assistente exclusivamente read-only e recusa solicitações destrutivas ou financeiras.
- Nenhum SQL livre, mutation, banco completo ou dado de outra empresa é exposto ao assistente.
- Nomes de produtos e clientes são tratados como dados, não como instruções.
- Rate limit local de 20 perguntas por minuto por usuário e conta.
- Perguntas limitadas a 500 caracteres, contexto agregado e histórico apenas na sessão do navegador.
- Logs não guardam o texto da pergunta nem dados pessoais desnecessários.

## API

- `GET /intelligence/forecast`
- `GET /intelligence/insights`
- `POST /intelligence/ask`

## Teste manual

1. Faça duas ou mais vendas de um produto e reduza seu estoque para verificar cobertura e risco.
2. Cadastre um lead time na relação produto-fornecedor e confira ponto de pedido e sugestão.
3. Abra Vendi Inteligente, filtre categoria/prioridade e use Como foi calculado.
4. Confira produtos parados, margens, aumentos de custo, perdas, validade e fiado conforme existirem dados.
5. Abra Pergunte ao Vendi e teste vendas, lucro, estoque, fiado e fornecedores.
6. Pergunte `Quanto vendi hoje?` e confira o período explícito e as fontes.
7. Entre como Caixa e pergunte `Quanto lucrei este mês?`; a informação deve ser bloqueada.
8. Pergunte `Apaga a dívida de Maria`; o assistente deve recusar sem alterar dados.

## Pendências

- Integração opcional com um LLM externo. O produto não depende dela e nenhuma chave foi configurada.
- Feedback útil/não útil e dispensa temporária de insights.
- Criação pré-preenchida de pedido em rascunho; nesta fase a ação navega para Compras para revisão manual.
- Timezone configurável por conta; os cálculos atuais seguem a data operacional do servidor.

## Próxima fase

**Fase 7 - Resiliência: Offline + Sincronização + Conflitos + Segurança + Backup + Estabilidade Operacional.**
