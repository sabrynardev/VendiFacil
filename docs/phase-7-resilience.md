# Fase 7 - Resiliência

## O que funciona

- O PDV detecta a disponibilidade real da API por `/health`, sem confiar apenas no indicador de rede do navegador.
- Produtos e a última sessão de caixa confirmada são armazenados no IndexedDB por empresa.
- O carrinho em andamento é salvo automaticamente e recuperado após recarregar ou reabrir a aplicação.
- Vendas comuns podem ser concluídas offline por até 12 horas após a última confirmação da sessão.
- A fila local é persistente, isolada por empresa e operador, sequencial e usa retentativa com backoff exponencial.
- Cada operação possui UUID, chave de idempotência e identificação do dispositivo. Reenvios não duplicam venda nem estoque.
- Preço alterado, produto inativo, caixa fechado e estoque negativo são aceitos com conflito explícito no histórico de sincronização.
- Produto removido, sessão expirada, fiado e desconto que exige gerente ficam em `REQUIRES_ATTENTION` e não são forçados.
- O comprovante offline é identificado como pendente e não fiscal.
- A tela `Sincronização` mostra pendências locais e confirmações seguras do servidor.

## Decisões de segurança

- Fiado, sangria, suprimento, abertura/fechamento de caixa e autorização gerencial exigem conexão.
- O backend recalcula regras críticas e nunca confia em totais ou permissões do frontend.
- Um preço offline diferente só é aceito quando a versão do produto prova que o catálogo mudou depois do cache; preço adulterado na mesma versão fica para revisão.
- A API limita tentativas de login e criação pública de conta.
- Em `APP_ENVIRONMENT=production`, segredo JWT fraco e `AUTO_SEED=true` impedem a inicialização.
- Respostas incluem identificador de correlação e cabeçalhos defensivos; erros inesperados não expõem detalhes internos.

## Conflitos

O servidor mantém a ordem local das operações por dispositivo. Estoque é serializado por produto durante a sincronização. Como disponibilidade é uma informação global, uma venda offline válida é preservada mesmo quando deixa o estoque negativo; o conflito fica registrado para revisão. Operações sem resolução automática permanecem no dispositivo até ação explícita.

## Backup e restauração

SQLite, a partir de `backend`:

```powershell
.venv\Scripts\python.exe scripts\backup.py
.venv\Scripts\python.exe scripts\restore.py ..\backups\vendi-AAAAMMDD-HHMMSS.db --confirm RESTORE
```

PostgreSQL usa a mesma interface e requer `pg_dump`/`pg_restore` disponíveis no `PATH`. Faça restaurações com o backend parado. Após restaurar, reinicie e confirme `database: ok` em `/health` antes de operar.

## Teste manual offline

1. Entre no PDV conectado, abra o caixa e aguarde o indicador `Online`.
2. Desligue o backend e aguarde o indicador mudar para `Offline`.
3. Busque um produto já sincronizado, monte e finalize uma venda PIX ou dinheiro.
4. Confira o comprovante `PENDENTE` e a operação em `Sincronização`.
5. Recarregue a página durante outro carrinho e confirme sua recuperação.
6. Coloque uma venda em espera offline, recupere-a e conclua-a.
7. Religue o backend e use `Sincronizar agora`.
8. Confirme a venda uma única vez em `Vendas`, a baixa única em `Estoque` e o registro no histórico de sincronização.

## Limitações conscientes

- A operação offline é limitada ao PDV e não tenta tornar todo o ERP offline.
- O service worker é ativado no build de produção; no servidor de desenvolvimento, o cache do aplicativo não é registrado.
- O custo usado no CMV é o custo vigente no servidor no momento da sincronização.
- Conflitos são sinalizados para análise; ainda não existe uma central administrativa para editar manualmente o conteúdo de uma operação.
- Tokens continuam no armazenamento local da aplicação. Para exposição pública, a evolução recomendada é cookie `HttpOnly`, HTTPS obrigatório e rotação de sessão.
