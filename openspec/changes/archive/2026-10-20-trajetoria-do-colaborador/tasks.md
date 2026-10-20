# Tasks

## 1. Backend

- [x] 1.1 `minha_trajetoria` GET (D1, D2). Verificar: `python tools/checar_endpoints.py` sem falhas.
  - **Feito (20/10/2026):** `checar_endpoints` 230, 0 falhas.
- [x] 1.2 `avaliacoes/{id}/competencias` GET (D3). Verificar: `python tools/checar_endpoints.py` sem falhas.
  - **Feito (20/10/2026):** idem.
- [x] 1.3 Publicar os dois endpoints. Verificar: dry-run só com 2 `CREATE`; depois do push, `tools/testar_trajetoria_http.py` com login de verdade.
  - **Publicado (20/10/2026):** dry-run com 2 `CREATE` e nada mais; o `pull` depois do push só difere na formatação. `tools/testar_trajetoria_http.py`: 10/10 (20/10/2026). O caso 200 de `avaliacoes/{id}/competencias` não rodou: a conta não tinha avaliação a preencher.

## 2. Frontend

- [x] 2.1 `api_client.py` e `trajetoria_modelo.py` (selos, textos de prazo, 360, validações). Verificar: casos de regra em `tools/testar_trajetoria.py`.
  - **Feito (20/10/2026):** 17 verificações de regra.
- [x] 2.2 `pagina_trajetoria.py` com os cinco blocos do Figma 64:42 e o menu em `app.py` (D4). Verificar: `tools/testar_trajetoria.py` (blocos, vazio, sem ficha, erro).
  - **Feito (20/10/2026):** 13 verificações da tela. O sino leva "avaliação disponível" à Trajetória.
- [x] 2.3 Modais: responder e enviar avaliação, contestar, check-in de meta e progresso do PDI (D4). Verificar: `tools/testar_trajetoria.py` (chamadas e recusas do backend).
  - **Feito (20/10/2026):** 14 verificações dos modais; 44/44 no total, no CI.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/figma-pendencias.md` (modais sem nó e o `user_id` em `avaliacoes/{id}`) e as tarefas 31 a 33 de `concluir-frontend-streamlit`. Verificar: `openspec validate trajetoria-do-colaborador`.
  - **Feito (20/10/2026):** seção 10.6 das regras; tarefas 31 e 32 feitas, 33 parcial (o mural fica com a 66).
