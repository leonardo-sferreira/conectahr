table regra_aplicada {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    int colaborador_id {
      table = "colaborador"
    }
    int? regra_contrato_id {
      table = "regra_contrato"
    }
    int? regra_override_id {
      table = "regra_override"
    }
    int? instrumento_normativo_id {
      table = "instrumento_normativo"
    }
    text processo_tipo filters=trim|max:50
    int processo_id
    text regra_aplicada_versao filters=trim|max:50
    json parametros_aplicados
    timestamp data_calculo
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
    {type: "btree", field: [{name: "processo_tipo", op: "asc"}]}
    {type: "btree", field: [{name: "data_calculo", op: "desc"}]}
  ]
}
