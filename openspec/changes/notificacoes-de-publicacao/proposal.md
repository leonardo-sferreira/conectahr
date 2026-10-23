# Proposal

## Why

Mapeamento de Leonardo (23/10/2026), a partir do uso do sistema. Hoje o sino só recebe o que passa pela central de pendências:
- o pedido novo, para quem decide (`ConectaHR/notificar_decisores`, tipo `pedido_novo`);
- o retorno do pedido (`pedido_decidido`);
- cadastro, documento, holerite e avaliação.

Quando o RH publica um treinamento novo ou abre uma pesquisa, ninguém é avisado; a pessoa só descobre se entrar na tela certa.

## What Changes

- **Treinamento novo** (D2): ao criar um treinamento ativo, ou ao reativar um inativo, avisar o público dele (todos ou os departamentos), menos quem publicou.
- **Pesquisa nova** (D3): avisar o público quando uma pesquisa fica disponível para resposta. Vale para a pesquisa de clima, a avaliação psicossocial da NR-1 e o termômetro de humor; a avaliação 360 já avisa. O convite não tem vínculo nenhum com a resposta.
- **Solicitação para decidir** (D4): conferir, tipo a tipo, que quem decide recebe `pedido_novo`, e fechar as lacunas: delegação e substituto.
- **Lembretes** (D5, opcional): treinamento obrigatório vencendo e pesquisa perto de encerrar, na rotina diária.
- **Preferências** (D6): os assuntos novos "Treinamentos" e "Pesquisas" em Configurações → Notificações, com opção de desligar.
- **Base** (D1): a função `ConectaHR/notificar_publico` e os tipos novos no enum de `notificacao_interna`.

## Non-goals

- E-mail dos avisos novos: não há modelo no Brevo para eles. Se a preferência de e-mail estiver ligada, nada é enviado por enquanto; fica para outra change.
- Avisar por WhatsApp, Teams ou Slack.
- Reatribuir uma solicitação a outra pessoa: o fluxo não existe hoje (D4).
- Disparo agendado: o plano do Xano não tem Background Tasks. O que depende de data roda na rotina diária, acionada por uma pessoa.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: avisos de publicação (treinamento e pesquisa), conferência dos avisos de decisão e preferências por assunto.

## Impact

- **Backend:**
  - enum `notificacao_interna.tipo`: `treinamento_novo` e `pesquisa_nova` (e, com o D5, `treinamento_vencendo` e `pesquisa_encerrando`);
  - enum `preferencia_aviso.assunto`: `treinamentos` e `pesquisas`;
  - função nova `ConectaHR/notificar_publico`;
  - campo `pesquisa_clima.convite_enviado_em`;
  - alterados: `treinamentos` POST, `treinamentos/{id}` PATCH, `pesquisas_clima/{id}/perguntas` POST, `ConectaHR/processar_transicoes_diarias`, `delegacoes` POST e `ConectaHR/notificar_decisores`.
- **Frontend:**
  - `configuracoes_modelo.py` (os assuntos);
  - `notificacoes_modelo.py` (o destino de cada tipo novo: "Meus treinamentos", "Pesquisa de clima", Início).
- **Figma:** Configurações → Notificações (213:236) ganha as duas linhas novas.
- **Testes:** `tools/testar_notificacoes.py`, `tools/testar_configuracoes.py` e um novo `tools/testar_notificacoes_publicacao_http.py`.
- **Documentação:**
  - `docs/regras-de-negocio.md`;
  - `docs/preferencias-notificacao.md`;
  - `docs/lgpd/registro-de-operacoes.md` (F16).
- **Depende de:** `termometro-de-humor` (PR #97) para o disparo do termômetro.
