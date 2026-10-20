# Tasks

## 1. Backend

- [x] 1.1 Função `ConectaHR/impacto_override` (D1). Verificar: dry-run só com `CREATE`.
  - **Feito (20/10/2026):** publicada (1 `CREATE`).
- [x] 1.2 `simular` com a função, conflitos, departamentos e o valor da matriz (D2). Verificar: `checar_endpoints` e dry-run com o `UPDATE` esperado.
  - **Feito (20/10/2026):** publicada (`UPDATE`; antes, conferido igual ao git).
- [x] 1.3 Conflito bloqueia em `enviar_aprovacao` e `aprovar`; `regras_override` GET com os conflitos; `aprovar` com justificativa (D3, D4). Verificar: idem.
  - **Feito (20/10/2026):** publicados (3 `UPDATE`). O encerramento da versão anterior em `aprovar` deixou de usar `||` no `where`.
- [x] 1.4 `regras_override/{id}/rejeitar` e `/prioridade` (D4). Verificar: `checar_endpoints` e dry-run com `CREATE`.
  - **Feito (20/10/2026):** publicados (2 `CREATE`); `checar_endpoints` 246, 0 falhas.
- [ ] 1.5 Publicar e rodar `tools/testar_regras_http.py` com login de verdade.
  - **Publicado (20/10/2026).** Falta rodar `tools/testar_regras_http.py` (pede o código que chega por e-mail).

## 2. Frontend

- [x] 2.1 `api_client.py` e `regras_modelo.py` (selos, ações por situação, filtros, histórico, simulação). Verificar: regras em `tools/testar_regras.py`.
  - **Feito (20/10/2026):** 16 verificações de regra.
- [x] 2.2 Lista, modais e simulação em `pagina_regras.py`, no menu (D5). Verificar: `tools/testar_regras.py`.
  - **Feito (20/10/2026):** 16 verificações de tela; 32/32 no CI.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/figma-pendencias.md` e as tarefas 36 e 37. Verificar: `openspec validate tela-de-regras`.
  - **Feito (20/10/2026):** regras de negócio, Figma e tarefas 36 e 37.
