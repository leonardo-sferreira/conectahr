# Proposal

## Why

A tela Trajetória (Figma 64:42; tarefas 31 a 33 da change `concluir-frontend-streamlit`) ainda não existe no Streamlit, e o usuário pediu (20/10/2026) que ela seja feita. O backend tem os endpoints de escrita (respostas, envio e contestação de avaliação, check-in de meta, progresso do PDI), mas faltam leituras de que a tela depende: o colaborador não consegue ver as avaliações feitas **sobre ele** (só as que ele preenche), não há lista das competências a responder numa avaliação e os reconhecimentos recebidos não trazem o nome de quem enviou.

## What Changes

- **`minha_trajetoria` GET** (grupo Colaboradores): numa chamada, o plano de carreira (nível atual, próximo nível e competências a desenvolver), o ciclo de avaliação em andamento, o 360 sobre a pessoa (autoavaliação, gestor com o nome, pares só com a contagem), as avaliações que ela tem a preencher, as enviadas sobre ela (com a contestação, se houver), as metas e o PDI ativos e os reconhecimentos recebidos com o nome de quem enviou (D1, D2).
- **`avaliacoes/{id}/competencias` GET**: só o avaliador; as competências do nível do avaliado e as respostas já salvas (D3).
- **Tela Trajetória** (todos os perfis com ficha de colaborador): os cinco blocos do Figma 64:42 e as ações responder e enviar avaliação, contestar avaliação recebida, check-in de meta e progresso do PDI (D4).

## Non-goals

- Mural de reconhecimentos, envio de reconhecimento e moderação (seção 16 do Figma; tarefa 66 da change `concluir-frontend-streamlit`).
- Telas do RH e do gestor para criar ciclos, atribuir avaliações, metas e PDI, e revisar contestações.
- Promoção: a tela só informa o próximo nível ("Sem promoção automática — decisão sempre humana").

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: novo requisito da tela Trajetória do colaborador, com o 360 sobre a pessoa, o anonimato dos pares e as ações de cada bloco.

## Impact

- Backend: `api/conecta_rh_colaboradores/minha_trajetoria_GET.xs` e `avaliacoes/id/competencias_GET.xs` (só leitura; nenhuma tabela nova).
- Frontend: `api_client.py`, `trajetoria_modelo.py` (regras puras), `pagina_trajetoria.py`, `app.py` (menu).
- Testes: `tools/testar_trajetoria.py` (AppTest, sem rede) e `tools/testar_trajetoria_http.py` (login de verdade).
- Documentação: `docs/regras-de-negocio.md`, `docs/figma-pendencias.md` e as tarefas 31 a 33 de `concluir-frontend-streamlit`.
