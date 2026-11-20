# Design

## Context

Ver proposal.md. Os e-mails de aviso (solicitação respondida, avaliação disponível, férias aprovadas, documento vencendo, alertas de segurança e troca de e-mail) são gravados em `email_outbox` com uma chave de idempotência e só saem por `email_outbox/processar`, que tenta cada um até 3 vezes pelo Brevo. O código de acesso do login e o "esqueci minha senha" saem na hora, sem fila. `status_operacional` já conta a fila, as tarefas manuais (desligamentos com data efetiva vencida, documentos vencidos), o que a rotina diária mudaria e as contas bloqueadas por senha.

## Decisions

### D1. Listar a fila

`email_outbox` GET, só RH e Admin, como `email_outbox/processar`:
- **Filtro:** `status` opcional (`pendente`, `enviado` ou `falhou`; vazio = todos; outro valor = 400).
- **Lista:** os 50 mais recentes, cada um com assunto, chave, destinatário mascarado, situação, tentativas, último erro, criado em e enviado em.
- **Destinatário mascarado no backend:** a primeira letra e o domínio (`p***@empresa.com`). O e-mail inteiro e o texto do e-mail não saem (minimização, LGPD art. 6º, III). O Admin identifica o caso pelo tipo e pela hora.
- **Contagens:** `na_fila` (pendentes), `enviados_24h` (por `enviado_em`) e `falharam_24h` (por `updated_at`).

### D2. Tela (Admin; Figma 249:7847)

- **Indicadores:** e-mails na fila, falharam (24h), enviados (24h) e contas bloqueadas por senha (de `status_operacional`).
- **"Processar fila agora":** fica desligado sem pendentes. O resultado mostra os enviados, os que deram erro (tentam de novo) e os desistidos.
- **Aba "Fila de e-mails":**
  - colunas: tipo (o nome legível da chave sem os números), destinatário mascarado, criado em (hoje, ontem ou data, no horário de Brasília), tentativas e situação;
  - a linha que falhou fica destacada, com o erro;
  - filtro de situação.
- **Aba "Tarefas manuais":**
  - rotina diária, com o total do que mudaria e "Rodar rotina";
  - desligamentos com data efetiva vencida: a rotina conclui; com o checklist incompleto, o caminho é "Abrir Desligamentos";
  - documentos vencidos, com "Processar documentos".

  Rodar de novo não repete nada.
- **Aba "Modelos":** o aviso do Figma ("Editar modelos ainda não tem endpoint no backend"), a explicação do modelo único e o link para o painel do Brevo.

## Risks / Trade-offs

- [Fila grande no processamento e o limite de 300 e-mails/dia do Brevo gratuito] → o processamento já registra a falha e tenta de novo na próxima vez.
- [Erro de execução do XanoScript] → `tools/testar_integracoes_http.py` com login (só leitura).

## Migration Plan

1. Endpoint novo (`CREATE`).

Rollback: apagar o endpoint.
