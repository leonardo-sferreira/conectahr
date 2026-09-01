# Auditoria — ConectaRH

Registro da auditoria obrigatória implementada e verificada (item 7.11): autenticação,
usuários, contratos, ponto, documentos, regras e avaliações. Cada evento registra
autor (`user_id`), data (`created_at`), recurso e registro afetados, valores
anterior/novo quando aplicável, justificativa quando aplicável, e resultado
(`sucesso`/`falha`) — nunca senha, token ou código de acesso.

## Endpoint de consulta

Antes desta tarefa, os eventos eram gravados mas não havia nenhum endpoint para
lê-los — gap encontrado durante os testes de segurança (item 7.3). Criado
`GET auditoria` (RH/ADMIN), com filtros opcionais por `recurso`, `registro_id`,
`user_id`, `acao` e `resultado`, ordenado do mais recente para o mais antigo.

## Cobertura por domínio

A tabela `auditoria` já era gravada em ~60 endpoints antes desta tarefa (aprovações,
rejeições, cancelamentos e outras transições de status em quase todos os domínios de
negócio). Um levantamento sistemático (todo endpoint `POST`/`PATCH`/`DELETE` do
backend) encontrou 42 endpoints de ação sem auditoria; desta lista, os que pertencem
aos domínios explicitamente citados pela tarefa foram cobertos nesta rodada:

- **Autenticação**: `auth/otp/reenviar` (reenvio de código de acesso).
- **Usuários**: `usuarios POST` (criação de acesso — evento crítico, antes não
  auditado) e `usuarios/{id} PATCH` (atualização de dados).
- **Contratos**: `colaboradores POST` (cadastro) e `contratos_especificos/{id} PATCH`
  (atualização de campos do contrato).
- **Ponto**: `ponto/marcar POST` — o mais sensível dos gaps encontrados (marcação de
  ponto nunca era auditada); a ação gravada distingue qual dos quatro marcadores
  (entrada/início de intervalo/fim de intervalo/saída) foi registrado.
- **Documentos**: `documentos POST` (cadastro), `documentos/{id} PATCH`
  (atualização) e `documentos/{id}/arquivar POST` (arquivamento) — aprovar/rejeitar já
  eram auditados antes.
- **Regras**: `instrumentos_normativos/{id}/enviar_aprovacao` e
  `regras_override/{id}/enviar_aprovacao` — as demais transições (aprovar, rejeitar,
  suspender, revogar) já eram auditadas antes.
- **Avaliações**: `avaliacoes/{id}/respostas POST` (nota atribuída por competência) —
  enviar e contestar já eram auditados antes.

Todos os 12 endpoints foram verificados ao vivo: cada ação gerou o evento esperado,
consultável pelo novo `GET auditoria`, sem nenhum campo sensível exposto.

## Fora do escopo desta rodada

- **Exportações**: a funcionalidade de exportação (item 7.7) ainda não existe no
  backend, então não há o que auditar ainda — fica pendente para quando 7.7 for
  implementada.
- **Domínios não citados explicitamente na tarefa**, ainda sem auditoria (30
  endpoints): férias (`solicitacoes`, `id PATCH`), ausências (`POST`, `id PATCH`,
  `id DELETE`), desligamento (`POST`, `iniciar_analise`), departamentos e cargos
  (`POST`/`PATCH`/`status PATCH`), pesquisa de clima, reconhecimentos, comunicados
  (já autoral no `criado_por`, mas sem evento de auditoria dedicado), FAQ, feriados,
  metas/PDI (checkin/concluir/progresso), `notificacoes/marcar_lida`,
  `email_outbox/processar`, `documentos/processar_vencimentos`,
  `documentos/{id} DELETE` (sempre bloqueado por design, mas a tentativa em si não é
  registrada). Todos já têm controle de permissão testado e confirmado (ver
  `docs/testes-integracao.md` e `docs/testes-seguranca.md`); falta só o registro
  formal do evento, uma melhoria incremental de rastreabilidade, não uma lacuna de
  segurança de acesso.
