# Tasks

## 1. Backend

- [x] 1.1 Tabelas `ciclo_metas`, `pergunta_meta`, `formulario_meta`, `resposta_meta` e `feedback_meta` (D1 a D4). Verificar: dry-run só com 5 `CREATE` de tabela.
  - **Feito (20/10/2026):** publicadas (dry-run com 5 `CREATE` de tabela e nada mais).
- [x] 1.2 `ciclos_metas` GET/POST e `ciclos_metas/{id}` PATCH; `perguntas_meta` GET/POST e `perguntas_meta/{id}` PATCH (D1, D2). Verificar: `checar_endpoints` sem falhas.
  - **Feito (20/10/2026):** `checar_endpoints` 242, 0 falhas.
- [x] 1.3 `meu_ciclo_metas` GET, `meu_ciclo_metas/{ciclo_id}/respostas` POST e `/enviar` POST (D3, D5). Verificar: `checar_endpoints` sem falhas.
  - **Feito (20/10/2026):** idem.
- [x] 1.4 `formularios_meta` GET, `formularios_meta/{id}` GET e `formularios_meta/{id}/feedback` POST (D4, D5). Verificar: `checar_endpoints` sem falhas.
  - **Feito (20/10/2026):** idem.
- [ ] 1.5 Publicar (tabelas, depois endpoints, só criações) e `tools/testar_ciclo_metas_http.py` com login de verdade.
  - **Publicado (20/10/2026):** tabelas e depois 12 endpoints, só criações; o pull confere. Falta rodar `tools/testar_ciclo_metas_http.py` (pede o código que chega por e-mail).

## 2. Frontend

- [x] 2.1 `api_client.py` e `ciclo_metas_modelo.py` (situação das etapas, validações, respostas alteradas). Verificar: casos de regra em `tools/testar_ciclo_metas.py`.
  - **Feito (20/10/2026):** 16 verificações de regra em `tools/testar_ciclo_metas.py`.
- [x] 2.2 "Metas do ciclo" e o bloco na Trajetória (D3, D5). Verificar: `tools/testar_ciclo_metas.py` (salvar, enviar, janela encerrada, etapa 2 sem etapa 1, feedback visível).
  - **Feito (20/10/2026):** 15 verificações (pessoa e Trajetória).
- [x] 2.3 "Ciclos de avaliação" do RH: ciclos, perguntas e formulários (D1, D2, D5). Verificar: `tools/testar_ciclo_metas.py`.
  - **Feito (20/10/2026):** 10 verificações.
- [x] 2.4 "Metas da equipe" com o feedback, menu e sino (D4, D5). Verificar: `tools/testar_ciclo_metas.py`.
  - **Feito (20/10/2026):** 9 verificações; 50/50 no total, no CI. O sino leva a etapa enviada à equipe e o feedback a "Metas do ciclo".

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md` e `docs/figma-pendencias.md`. Verificar: `openspec validate ciclo-de-metas`.
  - **Feito (20/10/2026):** regras 10.7; LGPD (F12 e as 5 tabelas; a lacuna anterior de 10 tabelas ficou registrada em Pendências); Figma.
