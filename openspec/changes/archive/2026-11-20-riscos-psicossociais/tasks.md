# Tasks

## 0. Figma

- [x] 0.1 Desenhar a seção 21 (545:1272): Resultado (545:1274), Plano de ação (548:1287), modais "Nova ação" (548:1592) e "Nova avaliação" (548:1916) e a escala de frequência da pessoa (548:1951) (D5). Verificar: prints dos nós.
  - **Feito (20/10/2026):** modo claro. Falta a versão escura (docs/figma-pendencias.md).

## 1. Backend

- [x] 1.1 `pesquisa_clima.tipo`, `pergunta_clima` com escala `frequencia`, `dimensao` e `sentido`; `acao_psicossocial` (D1, D3). Verificar: dry-run com `ADD_FIELD`, `UPDATE_FIELD` e `CREATE`.
  - **Feito (20/10/2026):** publicadas.
- [x] 1.2 `pesquisas_clima` POST e `perguntas` com tipo, dimensão e sentido; `minhas_pesquisas_clima` e `pesquisas_clima_rh` com o tipo; `acoes_psicossociais` GET, POST e `{id}` PATCH (D1, D3). Verificar: `checar_endpoints`, conferência com o que está no ar e dry-run.
  - **Feito (20/10/2026):** antes, conferido igual ao git; publicados; `checar_endpoints` 265, 0 falhas.
- [x] 1.3 Testar com login de verdade: criar uma avaliação psicossocial de teste, responder, encerrar, ver o mapa, criar e atualizar uma ação, baixar o relatório.
  - **Feito (20/11/2026):** pelo `api_client` e pelo `psicossocial_modelo` da tela, com uma conta do RH e uma de Colaborador. Avaliação 6 ("TESTE tarefa 1.3", abre e fecha no dia, mínimo 2): 16 perguntas na escala de frequência para as duas contas, segunda resposta recusada (400), Colaborador sem criar, sem ver o resultado e sem mudar a ação (403), 2 participantes, mapa com as 8 dimensões no setor e na empresa, ação criada e passada a "em andamento", relatório PGR gerado com participação, mapa e plano. 21/23: as 2 falhas eram do roteiro, que procurava a dimensão na lista da pessoa (ela só traz texto e escala, de propósito) e por isso respondeu tudo com 3 (risco 50 em todas); o caminho do risco alto e de "riscos sem ação" segue coberto por `tools/testar_riscos_psicossociais.py`.

## 2. Frontend

- [x] 2.1 `psicossocial_modelo.py` (questionário, risco, mapa, riscos sem ação, relatório) e `api_client.py`. Verificar: regras em `tools/testar_riscos_psicossociais.py`.
- [x] 2.2 "Riscos psicossociais" com as quatro abas, a escala de frequência na "Pesquisa de clima" e o clima do RH sem as avaliações psicossociais (D5). Verificar: `tools/testar_riscos_psicossociais.py`.
  - **Feito (20/10/2026):** 20/20.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 20), `docs/lgpd/registro-de-operacoes.md` (F15 e cobertura) e `docs/figma-pendencias.md`. Verificar: `openspec validate riscos-psicossociais`.
