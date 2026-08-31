// Outbox de e-mail (item 5.5): fila de notificacoes assincronas
// (decisoes de ferias, ausencia, documentos vencendo, avaliacao
// disponivel, solicitacoes respondidas — ver design.md, "Persistencia e
// integridade"), separada do envio sincrono ja usado no fluxo de login/
// redefinicao de senha. `chave_idempotencia` evita duplicar o mesmo
// evento logico se o endpoint que o originou for chamado mais de uma
// vez. Sem Background Tasks neste plano Xano — processamento manual via
// `email_outbox/processar POST`, mesmo padrao ja usado em desligamento/
// vencimento de documentos.
table email_outbox {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?

    text destinatario_email filters=trim|lower
    text? destinatario_nome filters=trim|max:150
    text assunto filters=trim|max:200
    text corpo filters=trim|max:5000
    enum status?=pendente {
      values = ["pendente", "enviado", "falhou"]
    }
    int tentativas?=0
    int max_tentativas?=3
    text? ultimo_erro filters=trim|max:1000
    text chave_idempotencia filters=trim|max:150
    timestamp? enviado_em
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
    {type: "btree|unique", field: [{name: "chave_idempotencia", op: "asc"}]}
  ]

  guid = "conectahr-email-outbox-0001"
}
