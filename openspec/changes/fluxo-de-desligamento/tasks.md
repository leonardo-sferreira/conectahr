# Tasks

## 1. Backend

- [x] 1.1 Tabela `desligamento_checklist` (D1). Verificar: dry-run só com `CREATE`.
  - **Feito (20/10/2026):** publicada (1 `CREATE`).
- [x] 1.2 `aprovar` cria os itens; `{id}/checklist/{item_id}` POST; `concluir` exige o checklist; `{id}` GET com o checklist (D1). Verificar: `checar_endpoints` e dry-run.
  - **Feito (20/10/2026):** publicados (`aprovar`, `concluir` e `{id}` GET alterados; `checklist/{item_id}` novo).
- [x] 1.3 `solicitacoes_desligamento` GET com status opcional, contagens e nomes (D2). Verificar: idem.
  - **Feito (20/10/2026):** publicado; antes, conferido igual ao git.
- [x] 1.4 POST, `minhas_solicitacoes_desligamento` e `cancelar` sem a restrição de perfil (D3). Verificar: idem.
  - **Feito (20/10/2026):** publicados; `checar_endpoints` 247, 0 falhas.
- [ ] 1.5 Publicar e rodar `tools/testar_desligamento_http.py` com login de verdade.
  - **Publicado (20/10/2026).** Falta rodar `tools/testar_desligamento_http.py` (pede o código que chega por e-mail).

## 2. Frontend

- [x] 2.1 `api_client.py` e `desligamento_modelo.py`. Verificar: regras em `tools/testar_desligamento.py`.
  - **Feito (20/10/2026):** 10 verificações de regra.
- [x] 2.2 "Pedir desligamento" e o caminho no Perfil (D4). Verificar: `tools/testar_desligamento.py`.
  - **Feito (20/10/2026):** 10 verificações.
- [x] 2.3 "Desligamentos" do RH com o checklist (D4). Verificar: `tools/testar_desligamento.py`.
  - **Feito (20/10/2026):** 12 verificações; 32/32 no CI.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 6), `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md` e a tarefa 54. Verificar: `openspec validate fluxo-de-desligamento`.
  - **Feito (20/10/2026):** regras (6.4 e 6.4.1), LGPD, Figma e tarefa 54.
