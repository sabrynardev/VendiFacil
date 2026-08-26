# VendiFácil Case Study

## Resumo

O VendiFácil é um sistema de PDV para mercadinhos e lojas de conveniência, criado para demonstrar domínio de produto, frontend, backend e regras de negócio reais. O objetivo foi construir uma experiência que parecesse um software comercial utilizável, e não apenas um projeto acadêmico com telas estáticas.

## Problema

Pequenos comércios precisam registrar vendas com rapidez, acompanhar estoque, identificar ruptura e enxergar a operação em tempo real sem depender de sistemas complexos demais para o porte da loja.

## Solução

O projeto entrega:

- autenticação com perfis
- operação de caixa com carrinho e pagamento simulado
- atualização automática de estoque
- registro de movimentação
- dashboard com indicadores e gráficos
- histórico de vendas
- previsão de ruptura e sugestão de reposição

## Decisões técnicas

- `React + TypeScript + Vite`: interface rápida, organizada e com tipagem forte
- `Tailwind CSS`: velocidade de construção visual com consistência
- `FastAPI`: API enxuta, moderna e produtiva
- `SQLAlchemy + Pydantic`: separação entre persistência e validação
- `JWT`: autenticação simples e adequada para o escopo
- `PostgreSQL`: base principal planejada para uso real

## Regra de negócio mais importante

A venda foi pensada como fluxo crítico do sistema:

1. validar o produto
2. verificar estoque disponível
3. criar venda e itens
4. reduzir estoque
5. registrar movimentação
6. impedir inconsistências com rollback em caso de falha

Esse ponto dá ao projeto uma camada de realismo importante para portfólio técnico.

## Resultado

O sistema permite demonstrar uma jornada completa:

- login
- consulta do catálogo
- operação de caixa
- fechamento da venda
- conferência de histórico
- impacto em estoque e dashboard

## O que este projeto comunica sobre o desenvolvedor

- capacidade de construir aplicações full stack completas
- cuidado com UX e aparência final
- compreensão de regras de negócio
- preocupação com testes e previsibilidade
- organização de código e separação de responsabilidades

## Próximas evoluções

- NFC-e
- PIX real
- múltiplos caixas
- multi-loja
- app mobile
- ERP
- fidelidade
- relatórios avançados
