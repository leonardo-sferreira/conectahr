# Sessões, alertas de acesso suspeito e monitoramento operacional — ConectaRH

Documentação da implementação do item 7.9.

## Sessões e dispositivos (já implementadas em sessão anterior)

- `GET auth/minhas_sessoes`: lista as sessões ativas do próprio usuário (dispositivo,
  data do último uso).
- `POST auth/sessoes/{id}/encerrar`: encerra uma sessão específica do próprio
  usuário (bloqueado para sessões de outro usuário — testado).
- `POST auth/sessoes/encerrar_outras`: encerramento seletivo — derruba todas as
  sessões exceto a atual.
- `POST auth/logout`: encerra a sessão atual.

Isolamento entre usuários confirmado ao vivo: um usuário não consegue listar nem
encerrar sessão de outro.

## Alertas de acesso suspeito (novo nesta tarefa)

Ao efetuar login com senha correta (`auth/login`), se a conta tinha 3 ou mais
tentativas de senha inválida registradas em `senha_tentativas_invalidas` (contador
do item 7.3) imediatamente antes desse acerto, o sistema:

1. Envia um e-mail de alerta ao titular da conta via `email_outbox` (assíncrono, não
   atrasa nem bloqueia o login).
2. Grava um evento de auditoria `alerta_acesso_suspeito`, com a quantidade de
   tentativas inválidas na justificativa.

O alerta é best-effort: não impede o login (a senha estava correta) nem exige
confirmação — é apenas notificação. Verificado ao vivo com conta descartável de
teste: 3 tentativas erradas seguidas de 1 acerto geraram o evento de auditoria com a
justificativa correta ("3 tentativas de senha invalida antes do login bem-sucedido")
e incrementaram a fila de e-mail.

## Monitoramento operacional — `GET status_operacional` (novo nesta tarefa)

Endpoint exclusivo de RH/ADMIN. Reporta:

- **`fila_email`**: contagem de `email_outbox` por status (`pendente`, `falhou`,
  `enviado`) — substitui a falta de um painel nativo de fila de e-mail da
  plataforma.
- **`tarefas_manuais_pendentes`**: quantidade de desligamentos agendados com data
  efetiva já vencida e ainda não concluídos manualmente, e de documentos aprovados
  com validade vencida ainda não reprocessados. Este projeto não tem acesso a
  Background Tasks (plano Xano gratuito, achado documentado em
  `conectahr_xano_platform_quirks`), então tarefas que seriam automáticas em um
  plano pago viram rotinas disparadas manualmente (`task/concluir_desligamentos_agendados`,
  `documentos/processar_vencimentos`); este bloco é o substituto do monitoramento
  de "falhas de tarefas" citado na tarefa — mede o atraso acumulado por essas
  rotinas não terem rodado ainda, não falhas de execução em si (não existe conceito
  de execução/falha sem Background Tasks).
- **`acesso_bloqueado`**: quantidade de contas atualmente com bloqueio de senha
  ativo (`senha_bloqueada_ate` no futuro).

Verificado ao vivo, incluindo o caso de borda de desbloqueio automático: uma conta
bloqueada anteriormente voltou a logar com sucesso após o TTL de 15 minutos expirar,
e uma nova conta bloqueada em seguida apareceu corretamente em
`acesso_bloqueado.contas_bloqueadas_por_senha`.

## Fora do escopo: backups e recuperação

Backups do banco de dados e recuperação de desastres são responsabilidade da
infraestrutura/plano de hospedagem do Xano — não há filtro, primitiva ou API em
XanoScript para acionar, listar ou restaurar backups a partir de código de
aplicação. Não há, portanto, nada a implementar ou expor nesta camada; é uma
responsabilidade de operação da plataforma, fora do alcance do backend
desenvolvido neste projeto.
