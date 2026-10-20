// Formulario de metas de uma pessoa num ciclo (change ciclo-de-metas, D3). Um por pessoa e ciclo;
// cada etapa enviada fica com a data e nao muda mais.
table formulario_meta {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int ciclo_metas_id {
      table = "ciclo_metas"
    }

    int colaborador_id {
      table = "colaborador"
    }

    timestamp? etapa1_enviada_em?
    timestamp? etapa2_enviada_em?
    timestamp? etapa3_enviada_em?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ciclo_metas_id", op: "asc"}, {name: "colaborador_id", op: "asc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]
  guid = "JqO0xGRvSg5QWghvKe25dybCr-0"
}
