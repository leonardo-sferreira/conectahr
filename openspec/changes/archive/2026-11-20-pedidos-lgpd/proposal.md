# Proposal

## Why

O usuário pediu (20/10/2026) os pedidos de LGPD. O titular já faz o pedido em Configurações → Privacidade (`solicitacao_rh` com tipo `privacidade_lgpd`, prazo de 15 dias), mas o RH não tem onde responder: o item "Pedidos LGPD" do menu ainda diz "em construção", e "Solicitações ao RH" não mostra esse tipo. O desenho (Figma 249:5709 e o modal 249:5955) pede três decisões (atendido, atendido em parte, não atendido) e uma resposta ao titular, mas o backend não guarda "atendido em parte" e aceita atender sem resposta.

## What Changes

- **Resultado e resposta** (D1):
  - novo campo `solicitacao_rh.resultado_lgpd`: `atendido`, `atendido_parcial` ou `nao_atendido`;
  - `solicitacoes/{id}/atender` aceita `resultado` (`parcial`) e, no pedido LGPD, exige a resposta ao titular;
  - `indeferir` grava `nao_atendido`.
- **Tela "Pedidos LGPD"** (D2): indicadores, abas "Abertos" e "Respondidos", filtro de tipo, tabela com o prazo e o modal "Responder pedido LGPD".
- **Titular** (D3): "Meus pedidos de privacidade" mostra "Atendido em parte" e a resposta do RH.

## Non-goals

- Status "em análise" pela tela (o backend não tem endpoint para assumir o pedido).
- Executar a correção ou a eliminação a partir da tela: o RH faz pelos caminhos que já existem (cadastro, anonimização) e responde.
- Prorrogar o prazo.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: resposta ao pedido do titular com resultado (inclusive parcial) e resposta obrigatória.

## Impact

- **Backend:** `solicitacao_rh` (campo novo), `solicitacoes/{id}/atender` e `solicitacoes/{id}/indeferir`.
- **Frontend:** `api_client.py`, `pedidos_lgpd_modelo.py`, `pagina_pedidos_lgpd.py`, `privacidade_modelo.py`, `app.py` e `theme.py`.
- **Testes:** `tools/testar_pedidos_lgpd.py`.
- **Documentação:** `docs/regras-de-negocio.md` e `docs/figma-pendencias.md`.
