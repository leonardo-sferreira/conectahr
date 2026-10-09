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

## Backup e recuperação

O Xano não tem, em XanoScript, uma primitiva para acionar ou restaurar o backup da plataforma; isso é
da hospedagem. O projeto, porém, mantém **o seu próprio backup**, em dois pedaços:

| Pedaço | Como | Contém dado pessoal? |
|---|---|---|
| **Código e schema** (tabelas, funções, endpoints, grupos) | O repositório Git (`xano-workspace/`) é a fonte; `xano workspace pull -p ConectaRH -d <pasta>` baixa o estado real do Xano | Não |
| **Dados** (registros das tabelas) | `xano workspace pull -p ConectaRH --records -d <pasta>` | **Sim**: guarde fora do repositório, em local protegido, e nunca cole em ferramenta externa |

### Procedimento

1. **Rotina:** antes de cada publicação grande e ao menos uma vez por semana, rodar o `pull` de código
   e conferir que não há diferença de conteúdo em relação ao repositório (só formatação).
2. **Dados:** o `pull --records` só quando necessário (antes de uma mudança de schema destrutiva ou de
   uma limpeza). A pasta resultante fica fora do Git (o `.gitignore` não cobre `pr_*` ou pastas
   temporárias: escolha um caminho fora do repositório).
3. **Restauração:** `xano workspace push -p ConectaRH -d <pasta-do-backup> --sync`. Em outro workspace
   (plano pago), acrescentar `-w <ID>`; para os dados, `--records` (depois de conferir o destino).
   Reconfigurar as variáveis de ambiente do Xano no destino (as chaves não vão no backup).
   **Prove a restauração antes com `--dry-run`:** o resultado "No changes to push" mostra que o
   backup recria exatamente o estado atual. O plano gratuito tem um workspace só, então não dá para
   restaurar num workspace vazio de teste.
4. **Depois de restaurar:** rodar `tools/checar_endpoints.py`, fazer um login de teste e conferir a
   contagem de objetos (tabelas, funções, endpoints).

### Situação do teste de restauração

O backup de código e schema foi baixado e comparado com o repositório, e a restauração foi
**simulada com `--dry-run` sobre o workspace real**, com resultado "No changes to push" (ver
[`evidencias/backup.md`](evidencias/backup.md)). A restauração **de verdade**, num workspace vazio,
não foi feita porque o plano gratuito só permite um workspace; fica como pendência para o dia em
que houver um segundo. A restauração dos **registros** (dados) também não foi exercitada.

