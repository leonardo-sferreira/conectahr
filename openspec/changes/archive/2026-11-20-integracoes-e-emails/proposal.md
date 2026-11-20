# Proposal

## Why

O usuário pediu (20/10/2026) a tela "Integrações e e-mails" (Figma 249:7847), item do grupo Admin que ainda diz "em construção". Sem ela, os e-mails de aviso ficam parados na fila (`email_outbox`): o plano do Xano não roda tarefas agendadas, e nenhuma tela aciona `email_outbox/processar`. A rotina diária e os documentos vencidos também só rodam por chamada manual. O backend tem as contagens (`status_operacional`) e o processamento, mas não lista a fila.

## What Changes

- **Fila** (D1): `email_outbox` GET (RH e Admin) com os 50 mais recentes, filtro de situação, o destinatário mascarado no próprio backend e as contagens das últimas 24 horas.
- **Tela** (D2): indicadores, "Processar fila agora", abas "Fila de e-mails", "Tarefas manuais" (rodar a rotina diária e processar documentos vencidos) e "Modelos" (aviso e link para o Brevo).

## Non-goals

- Editar os modelos de e-mail (ficam no Brevo).
- Reenviar um e-mail que desistiu depois de 3 tentativas.
- Agendar a fila ou a rotina (o plano não permite).

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: consulta da fila de e-mails com o destinatário mascarado.

## Impact

- **Backend:** `email_outbox` GET (novo).
- **Frontend:** `api_client.py`, `integracoes_modelo.py`, `pagina_integracoes.py`, `app.py` e `theme.py`.
- **Testes:** `tools/testar_integracoes.py` e `tools/testar_integracoes_http.py`.
- **Documentação:** `docs/regras-de-negocio.md` (1.6) e `docs/figma-pendencias.md`.
