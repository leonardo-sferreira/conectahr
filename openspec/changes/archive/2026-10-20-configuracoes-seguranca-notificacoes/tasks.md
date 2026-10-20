# Tasks

## 1. Segurança

- [x] 1.1 `auth/minhas_sessoes` com `sessao_atual_id` e `auth/senha` encerrando as outras sessões (D1). Verificar: `checar_endpoints` e dry-run só com 2 `UPDATE`.
  - **Feito (20/10/2026):** publicados (2 `UPDATE`); antes, conferido que o que estava no ar era igual ao git.
- [x] 1.2 Aba Segurança: trocar senha com as regras e sessões e dispositivos (D1). Verificar: `tools/testar_configuracoes.py`.
  - **Feito (20/10/2026):** `tools/testar_configuracoes.py` (9 verificações de Segurança).

## 2. Notificações

- [x] 2.1 Tabela `preferencia_aviso` e `minhas_preferencias_aviso` GET/PATCH (D2). Verificar: dry-run com `CREATE` e `checar_endpoints`.
  - **Feito (20/10/2026):** publicados (tabela; 2 `CREATE`).
- [x] 2.2 `notificar` e os avisos e e-mails dos seis endpoints respeitam a preferência (D3). Verificar: dry-run só com os `UPDATE` esperados e `checar_endpoints`.
  - **Feito (20/10/2026):** publicados (6 `UPDATE` de endpoint e 1 da função), conferidos contra o git antes e pelo pull depois; `checar_endpoints` 244, 0 falhas. `ponto/marcar` ficou de fora (REP-P; alerta legal).
- [x] 2.3 Aba Notificações (D2). Verificar: `tools/testar_configuracoes.py`.
  - **Feito (20/10/2026):** 8 verificações de Notificações; 22/22 no total, no CI.
- [x] 2.4 Publicar e `tools/testar_configuracoes_http.py` com login de verdade.
  - **Publicado (20/10/2026).** `tools/testar_configuracoes_http.py`: 8/8 (20/10/2026).

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md` e `docs/figma-pendencias.md`. Verificar: `openspec validate configuracoes-seguranca-notificacoes`.
  - **Feito (20/10/2026):** regras (auth e a seção nova de preferências), LGPD (F16 e a tabela) e Figma.
