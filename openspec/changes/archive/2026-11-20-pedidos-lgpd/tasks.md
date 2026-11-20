# Tasks

## 1. Backend

- [x] 1.1 `solicitacao_rh.resultado_lgpd`; `atender` com `resultado` e resposta obrigatória no pedido LGPD; `indeferir` com `nao_atendido` (D1). Verificar: `checar_endpoints`, dry-run (`ADD_FIELD` e dois `UPDATE`) e conferência com o que está no ar.
  - **Feito (20/10/2026):** publicados; antes, conferido igual ao git; `checar_endpoints` 253, 0 falhas.
- [x] 1.2 Responder pela tela um pedido de teste com cada decisão e conferir a resposta em Configurações → Privacidade.
  - **Feito (20/11/2026):** pelo `api_client` e pelos modelos da tela (`pedidos_lgpd_modelo`, `privacidade_modelo`), com uma conta de Colaborador e uma do RH. Pedidos de teste 6, 7 e 8: atendido, atendido em parte e não atendido; `resultado_lgpd` gravado, aba "Respondidos" com o selo certo, e o titular vê "Concluído", "Atendido em parte" e "Recusado" com "Resposta do RH: ...". Recusas: atender sem resposta (400), o próprio titular decidir (403) e decidir de novo (400). 26/26.

## 2. Frontend

- [x] 2.1 `api_client.py` (`parcial`), `pedidos_lgpd_modelo.py` e a resposta em `privacidade_modelo.py` (D3). Verificar: regras em `tools/testar_pedidos_lgpd.py`.
  - **Feito (20/10/2026):** 9 verificações de regra.
- [x] 2.2 "Pedidos LGPD" no menu do RH (D2). Verificar: `tools/testar_pedidos_lgpd.py`.
  - **Feito (20/10/2026):** 15 verificações de tela; 24/24; privacidade (108), solicitações (35), decisões (64) e configurações (22) seguem passando.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` e `docs/figma-pendencias.md`. Verificar: `openspec validate pedidos-lgpd`.
