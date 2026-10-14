# Proposal

## Why

O gestor decide as férias da equipe, mas não tinha onde ver, de uma vez, quem já vai sair em cada dia. A decisão de um pedido mostrava só quantos colegas do departamento estavam de férias no período (`ferias/{id}/verificar_conflito`), sem nome e sem a visão do mês. O usuário pediu (13/10/2026) que o gestor veja na tela de Férias o calendário com o nome de quem está abaixo dele e os dias de cada um, do início ao fim, para não deixar muita gente sair ao mesmo tempo.

## What Changes

- **Endpoint novo `ferias_equipe` (GET):** férias aprovadas, concluídas e em análise que tocam um período (`desde`, `ate`), com o nome de cada pessoa, no escopo da hierarquia da folha de ponto (D1).
- **Aba "Férias da equipe"** na tela Férias, para Gestor, RH, Admin e quem é superior direto de alguém: calendário do mês com os nomes em cada dia, setas de mês, a lista de quem sai no mês e um alerta quando o número de pessoas de férias no mesmo dia chega ao limite escolhido na tela (D2).

## Non-goals

- Bloquear a aprovação quando o limite é atingido: o limite é um alerta para o gestor, não uma regra do backend.
- Ausências e atestados no calendário da equipe (dado de saúde; o calendário mostra só férias).
- Filtro por departamento para o RH.

## Impact

- Backend: `api/conecta_rh_ferias/ferias_equipe_GET.xs` (novo, só leitura).
- Frontend: `api_client.ferias_equipe`, `ferias_modelo` (calendário, pico, lista e alerta da equipe), `pagina_ferias.py`, `theme.py` (nomes no calendário e borda do dia acima do limite).
- Documentação: `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`.
