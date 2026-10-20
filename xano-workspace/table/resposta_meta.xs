// Resposta de uma pergunta no formulario de metas (change ciclo-de-metas, D3). Etapa 1: a meta;
// etapas 2 e 3: o que foi alcancado e a autoavaliacao. Guarda o texto da pergunta da epoca.
table resposta_meta {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int formulario_meta_id {
      table = "formulario_meta"
    }

    int pergunta_meta_id {
      table = "pergunta_meta"
    }

    text pergunta_texto filters=trim|max:300
    int? ordem
    text? meta filters=trim|max:2000
    text? alcancado_etapa2 filters=trim|max:2000
    enum? autoavaliacao_etapa2 {
      values = ["abaixo", "dentro", "acima"]
    }

    text? alcancado_etapa3 filters=trim|max:2000
    enum? autoavaliacao_etapa3 {
      values = ["abaixo", "dentro", "acima"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "formulario_meta_id", op: "asc"}, {name: "pergunta_meta_id", op: "asc"}]}
  ]
  guid = "hKUYP4pZ8Ax10XxxLDMiIO_8o-0"
}
