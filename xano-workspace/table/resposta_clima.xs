// Resposta 100% anonima: nao guarda colaborador_id nem user_id, so
// departamento_id (capturado no momento da resposta, so para permitir
// agrupamento) e a nota. Nao ha como ligar uma linha desta tabela a
// uma pessoa especifica, nem para RH/ADMIN.
table resposta_clima {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    int pergunta_clima_id {
      table = "pergunta_clima"
    }
    int? departamento_id {
      table = "departamento"
    }
    int nota filters=min:1|max:5
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "pergunta_clima_id", op: "asc"}]}
  ]

  guid = "conectahr-resposta-clima-0001"
}
