# Preferências de notificação — ConectaRH

Documentação da implementação do item 7.8: preferências de canal e frequência de
notificação, sem permitir desativar avisos obrigatórios de segurança.

## Desenho

Notificação interna (tabela `notificacao_interna`) **nunca é opcional** — todo
evento notificável sempre gera uma, independentemente de qualquer preferência,
conforme já estabelecido pelo item 5.11. As preferências desta tarefa controlam
apenas o **canal de e-mail** (`email_outbox`) e uma **frequência** declarada
(imediato/resumo diário/resumo semanal) por tipo de evento.

## Alertas obrigatórios — nunca desativáveis

Código de acesso de login, redefinição de senha e alerta de acesso suspeito
**não existem como valor do enum `tipo_evento`** da tabela `preferencia_notificacao`.
Isso significa que a garantia "sem desativar alertas obrigatórios de segurança" é
estrutural — bloqueada pelo domínio do dado, não apenas por uma checagem de código
que poderia ser contornada ou esquecida em um novo endpoint. Esses três continuam
sendo enviados sempre, sem checar preferência nenhuma (código inalterado).

## Endpoints

- **`GET minhas_preferencias_notificacao`**: retorna a preferência de cada um dos 5
  tipos de evento configuráveis (`documento_vencendo`, `solicitacao_respondida`,
  `avaliacao_disponivel`, `ferias_aprovada`, `documento_pendente`). Quando o usuário
  nunca configurou um tipo, retorna o padrão (`canal_email: true`,
  `frequencia: "imediato"`) sem persistir nada.
- **`PATCH minhas_preferencias_notificacao`**: atualiza um tipo de evento por vez.
  `canal_email` e `frequencia` são **obrigatórios** no input (não opcionais) —
  decisão deliberada para evitar o quirk confirmado desta plataforma onde
  `false`/`""` em campos opcionais são coagidos para `null` em comparações
  `==`/`!=` (ver `conectahr_xano_platform_quirks`, achado 19): se `canal_email`
  fosse opcional, um PATCH explícito para desativar e-mail (`canal_email: false`)
  poderia ser tratado como "não informado" e silenciosamente ignorado. Cada
  alteração é auditada.

## Frequência: resumo diário/semanal

O valor de `frequencia` é armazenado e retornado normalmente, mas a
**agregação/batching real de um resumo diário ou semanal não foi implementada**
nesta rodada — geraria a mesma dependência de rotina automática recorrente que já
bloqueia outras partes do projeto (documentos vencendo, desligamentos agendados):
este plano Xano não tem Background Tasks, e o usuário optou por não fazer upgrade.
A preferência fica pronta para ser honrada por um job de resumo assim que essa
capacidade existir; por ora, todo e-mail enviado é imediato, independentemente do
valor de `frequencia` salvo.

## Cobertura da checagem de canal_email

Conectado em 2 dos 6 pontos de criação de `email_outbox` do projeto, como prova de
conceito verificada ao vivo:

- `ferias/{id}/aprovar` (tipo `ferias_aprovada`)
- `avaliacoes POST` (tipo `avaliacao_disponivel`)

Os outros 4 pontos (`documentos/processar_vencimentos` — `documento_vencendo`,
`solicitacoes/{id}/atender` e `.../indeferir` — `solicitacao_respondida`,
`pendencias_documento POST` — `documento_pendente`) **ainda não checam a
preferência** — continuam enviando e-mail sempre, mesmo que o usuário tenha
desativado o canal para aquele tipo. Gap consciente, documentado em vez de
absorvido silenciosamente: replicar a mesma checagem nesses 4 pontos é mecânico
(mesmo padrão de `db.query preferencia_notificacao` + `conditional` já usado nos 2
pontos cobertos), mas não foi feito nesta rodada para manter o escopo do que foi
testado ao vivo.

## Verificado ao vivo

- `GET` sem preferência configurada retorna os 5 padrões corretos.
- `PATCH` desativando e-mail de `ferias_aprovada` e mudando para `resumo_semanal`
  persiste corretamente (confirmado por `GET` subsequente).
- `PATCH` tentando configurar `alerta_acesso_suspeito` (tipo obrigatório) é
  rejeitado com `ERROR_CODE_INPUT_ERROR`.
- Fluxo completo: com o canal de e-mail desativado para `ferias_aprovada`, uma
  aprovação real de férias (id 5) **não** criou entrada em `email_outbox`
  (`fila_email.pendente`/`enviado` inalterados em `status_operacional`), mas a
  notificação interna correspondente **foi** criada normalmente
  (`GET minhas_notificacoes` retornou o evento `ferias_aprovada` id 9) — confirma
  que a garantia "notificação interna nunca é opcional" se mantém mesmo com o
  e-mail desativado.
