# Proposal

## Why

O projeto tinha quatro changes abertas ao mesmo tempo: `conectarh.gestao`, `implementar-frontend-streamlit`, `corrigir-brechas-e-alinhar-documentacao` e `adequacao-lgpd`. Nenhuma estava arquivada. Por isso `openspec/specs/` continuava vazio, e a spec principal do sistema não existia fora das changes.

Para sincronizar a spec principal, as quatro precisam ser arquivadas, na ordem em que uma depende da outra. Mas juntas elas tinham 120 tarefas pendentes, e arquivar com tarefas abertas faria o trabalho restante sumir do rastreio.

Esta change resolve isso:
- **recebe todas as tarefas pendentes**, cada uma com a identificação da tarefa de origem;
- as quatro changes são arquivadas, e a spec principal `openspec/specs/conectahr/spec.md` passa a existir;
- o trabalho restante continua rastreado num único lugar, o `tasks.md` desta change.

## What Changes

- Esta change recebe 118 tarefas pendentes. Cada uma leva a origem entre colchetes:
  - `[GE x.y]` para `conectarh.gestao`;
  - `[FE x.y]` para `implementar-frontend-streamlit`;
  - `[CB x.y]` para `corrigir-brechas-e-alinhar-documentacao`;
  - `[LG x.y]` para `adequacao-lgpd`.
- Duas tarefas de origem são concluídas pela própria consolidação, e não movidas: `[CB 6.2]` e `[LG 5.2]`, que pediam para validar a change e respeitar a ordem de arquivamento.
- Também entram tarefas novas, identificadas no Figma e na análise do clima em 07/10/2026:
  - troca de senha no primeiro acesso como Passo 3 do login;
  - alertas dentro do card;
  - painel de notificações e menu da conta;
  - telas de Configurações;
  - supressão de vazamentos nos resultados da pesquisa de clima.
- Nas quatro changes de origem, cada tarefa pendente perde a caixa de seleção e passa a indicar para qual tarefa desta change foi movida. O texto original é preservado como histórico.
- As quatro changes são arquivadas na ordem `conectarh.gestao` → `implementar-frontend-streamlit` → `corrigir-brechas-e-alinhar-documentacao` → `adequacao-lgpd`.

**Non-goals**
- Implementar agora qualquer uma das tarefas movidas. Esta change só organiza; a execução vem nas próximas aplicações.
- Alterar requisitos. O comportamento esperado continua sendo o das specs das quatro changes, consolidado em `openspec/specs/conectahr/spec.md`.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. Esta change não altera requisitos (`skip_specs: true`). As tarefas implementam requisitos que já estão na spec principal depois do arquivamento das quatro changes.

## Impact

- **OpenSpec:**
  - nasce `openspec/specs/conectahr/spec.md`;
  - as quatro changes vão para `openspec/changes/archive/2026-10-08-<nome>/`;
  - `openspec list` passa a mostrar só esta change aberta.
- **Referências nas tarefas:** quando uma tarefa cita "a tarefa X.Y da `corrigir-brechas`", isso equivale a `[CB X.Y]` aqui. Quando cita o `tasks.md` ou o `design.md` de uma change de origem, o arquivo passa a estar na pasta `archive/` correspondente (ver `design.md`).
- **Código:** nenhuma alteração.
