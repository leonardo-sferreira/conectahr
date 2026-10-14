# Tasks

## 1. Backend

- [x] 1.1 `ferias_equipe` GET com a guarda do checklist, o escopo de D1 e o filtro por sobreposição. Verificar: `checar_endpoints` e a lógica rodada pela CLI com dados reais.
  - **Feito (14/10/2026):** publicado; `checar_endpoints` 224, 0 falhas. A mesma lógica, rodada na função temporária: visão do RH com as 6 pessoas visíveis; visão de um gestor sem subordinados só com ele mesmo; período de 01/12 a 31/12 e o dia 16/12 trazem as férias de 30/11 a 16/12, e 17/12 a 31/01 e 01/10 a 29/11 não trazem. HTTP com token: não verificado (código por e-mail).

## 2. Frontend

- [x] 2.1 Aba "Férias da equipe" (D2). Verificar: `tools/testar_ferias.py`.
  - **Feito (14/10/2026):** 93/93 (24 novas: nomes curtos, "+1", pedido em análise contando, rejeitada fora, pico, alerta com o limite 2 e sem alerta com 5, lista do mês, aba só para quem tem equipe, RH sem cadastro, erro do backend e troca de mês).

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md` e `docs/figma-pendencias.md`.
