# Proposal

## Why

Em Configurações, as abas "Segurança" (Figma 213:142) e "Notificações" (213:236) mostram "em construção" (pedido do usuário, 20/10/2026). O backend de senha e sessões já existe, mas não diz qual é a sessão atual e a troca de senha não encerra as outras sessões, como o desenho promete. As preferências de notificação existentes cobrem só o e-mail de cinco tipos de evento e são consultadas por dois endpoints; os avisos do sino ignoram qualquer preferência.

## What Changes

- **Segurança** (D1): "Trocar senha" com as três regras do Figma e "Sessões e dispositivos" (as sessões ativas, "Este dispositivo", "Encerrar" e "Encerrar todas as outras sessões").
  - `auth/minhas_sessoes` devolve também `sessao_atual_id`.
  - `auth/senha` (PATCH) encerra as outras sessões ativas da pessoa ao trocar a senha, e audita quantas.
- **Notificações** (D2, D3): por assunto, "Na plataforma" e "E-mail".
  - Tabela `preferencia_aviso` e os endpoints `minhas_preferencias_aviso` GET e PATCH.
  - A função `notificar`, os avisos gravados direto e os e-mails configuráveis passam a respeitar a preferência.
  - Benefícios, alertas de segurança e pedidos que esperam a decisão da pessoa continuam sempre ligados.

## Non-goals

- "Comunicados" e "Frequência dos e-mails" (resumo diário) do Figma: hoje nenhum aviso de comunicado é enviado e não há rotina de resumo. Ficam registrados em `docs/figma-pendencias.md`.
- Localização da sessão (cidade): o sistema guarda só o IP e o navegador.
- Apagar as preferências antigas (`preferencia_notificacao`) e seus endpoints: deixam de ser consultadas, sem migração.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: requisitos de Configurações (segurança da conta e preferências de aviso por assunto e canal).

## Impact

- Backend: `auth/minhas_sessoes_GET`, `auth/senha_PATCH`; tabela `preferencia_aviso`; `minhas_preferencias_aviso` GET/PATCH; função `ConectaHR/notificar`; avisos e e-mails em `avaliacoes_POST`, `solicitacoes/{id}/atender` e `indeferir`, `ferias/{id}/aprovar`, `documentos/processar_vencimentos` e `folha_ponto/tratar`.
- Frontend: `api_client.py`, `configuracoes_modelo.py`, `pagina_configuracoes.py`.
- Testes: `tools/testar_configuracoes.py` (AppTest) e `tools/testar_configuracoes_http.py`.
- Documentação: `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`.
