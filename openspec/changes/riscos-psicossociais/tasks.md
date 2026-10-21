# Tasks

## 0. Figma

- [x] 0.1 Desenhar a seção 21 (545:1272): Resultado (545:1274), Plano de ação (548:1287), modais "Nova ação" (548:1592) e "Nova avaliação" (548:1916) e a escala de frequência da pessoa (548:1951) (D5). Verificar: prints dos nós.
  - **Feito (20/10/2026):** modo claro. Falta a versão escura (docs/figma-pendencias.md).

## 1. Backend

- [x] 1.1 `pesquisa_clima.tipo`, `pergunta_clima` com escala `frequencia`, `dimensao` e `sentido`; `acao_psicossocial` (D1, D3). Verificar: dry-run com `ADD_FIELD`, `UPDATE_FIELD` e `CREATE`.
  - **Feito (20/10/2026):** publicadas.
- [x] 1.2 `pesquisas_clima` POST e `perguntas` com tipo, dimensão e sentido; `minhas_pesquisas_clima` e `pesquisas_clima_rh` com o tipo; `acoes_psicossociais` GET, POST e `{id}` PATCH (D1, D3). Verificar: `checar_endpoints`, conferência com o que está no ar e dry-run.
  - **Feito (20/10/2026):** antes, conferido igual ao git; publicados; `checar_endpoints` 265, 0 falhas.
- [ ] 1.3 Testar com login de verdade: criar uma avaliação psicossocial de teste, responder, encerrar, ver o mapa, criar e atualizar uma ação, baixar o relatório.

## 2. Frontend

- [x] 2.1 `psicossocial_modelo.py` (questionário, risco, mapa, riscos sem ação, relatório) e `api_client.py`. Verificar: regras em `tools/testar_riscos_psicossociais.py`.
- [x] 2.2 "Riscos psicossociais" com as quatro abas, a escala de frequência na "Pesquisa de clima" e o clima do RH sem as avaliações psicossociais (D5). Verificar: `tools/testar_riscos_psicossociais.py`.
  - **Feito (20/10/2026):** 20/20.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 20), `docs/lgpd/registro-de-operacoes.md` (F15 e cobertura) e `docs/figma-pendencias.md`. Verificar: `openspec validate riscos-psicossociais`.
