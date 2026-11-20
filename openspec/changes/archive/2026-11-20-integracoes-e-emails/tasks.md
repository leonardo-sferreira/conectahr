# Tasks

## 1. Backend

- [x] 1.1 `email_outbox` GET com o destinatário mascarado, o filtro e as contagens de 24 horas (D1). Verificar: `checar_endpoints` e dry-run só com 1 `CREATE`.
  - **Feito (20/10/2026):** publicado; sem token responde 401; `checar_endpoints` 254, 0 falhas.
- [x] 1.2 Rodar `tools/testar_integracoes_http.py` com login de verdade (conta do RH ou do Admin).
  - **Feito (20/10/2026):** 8/8 com conta do Admin. A primeira rodada pegou o filtro de situação recusado (400): o filtro de entrada `to_lower` não existe (o nome é `lower`); corrigido aqui e nos mesmos casos de `solicitacoes/{id}/atender` (`resultado`) e `pesquisas_clima/{id}/perguntas` (`escala`).

## 2. Frontend

- [x] 2.1 `api_client.py` e `integracoes_modelo.py`. Verificar: regras em `tools/testar_integracoes.py`.
  - **Feito (20/10/2026):** 7 verificações de regra.
- [x] 2.2 "Integrações e e-mails" no menu do Admin (D2). Verificar: `tools/testar_integracoes.py`.
  - **Feito (20/10/2026):** 11 verificações de tela; 18/18.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (1.6) e `docs/figma-pendencias.md`. Verificar: `openspec validate integracoes-e-emails`.
