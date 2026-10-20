# Tasks

## 1. Backend

- [x] 1.1 Tabelas: `pergunta_clima.escala`, faixa de 0 a 10 em `resposta_clima_agregado` e `comentario_clima` (D1). Verificar: dry-run com `CREATE`, `ADD_FIELD` e `UPDATE_FIELD`.
  - **Feito (20/10/2026):** publicadas.
- [x] 1.2 `minhas_pesquisas_clima` GET e `pesquisas_clima/{id}/responder` POST; faixa pela escala no endpoint por pergunta (D2). Verificar: `checar_endpoints` e dry-run.
  - **Feito (20/10/2026):** publicados.
- [x] 1.3 `pesquisas_clima_rh` GET; perguntas no POST; incluir pergunta só antes de abrir; resultados com favoráveis, departamentos e comentários (D3 e D4). Verificar: idem; conferido igual ao git antes.
  - **Feito (20/10/2026):** publicados.
- [x] 1.4 `ciclos_avaliacao_rh` GET, `ciclos_avaliacao/{id}/avaliacoes` GET, `ciclos_avaliacao/{id}/atribuir` POST e o status cancelando as em aberto (D5 a D7). Verificar: idem.
  - **Feito (20/10/2026):** publicados; `checar_endpoints` 253, 0 falhas.
- [ ] 1.5 Rodar `tools/testar_clima_avaliacao_http.py` com login de verdade (uma conta do RH e uma que não seja).
  - Falta rodar (pede o código que chega por e-mail).

## 2. Frontend

- [x] 2.1 `api_client.py`, `clima_modelo.py` e `avaliacao_ciclo_modelo.py`. Verificar: regras em `tools/testar_clima_avaliacao.py`.
  - **Feito (20/10/2026):** regras da pesquisa e do ciclo.
- [x] 2.2 "Pesquisa de clima" e o item no menu (D8). Verificar: `tools/testar_clima_avaliacao.py`.
  - **Feito (20/10/2026):** 10 verificações.
- [x] 2.3 "Pesquisas de clima" do RH (D8; Figma 249:4645 e 249:4885, com a adesão por departamento em `pesquisas_clima_rh`). Verificar: idem.
  - **Feito (20/10/2026):** 11 verificações.
- [x] 2.4 Aba "Avaliações de desempenho" em "Ciclos de avaliação" (D8; Figma F27 249:5068 e 249:5364, com as contagens por relação e o e-mail no lote). Verificar: idem.
  - **Feito (20/10/2026):** 9 verificações de tela e 4 de regra; 52/52 no total; as outras 28 suítes do CI seguem passando.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md` e a tarefa 48. Verificar: `openspec validate pesquisa-clima-e-avaliacao-360`.
  - **Feito (20/10/2026):** regras (10.3, 10.4, 10.8, 11.3, 11.4 e 11.7), LGPD (F15 e cobertura 58 de 68), Figma e tarefa 48.
