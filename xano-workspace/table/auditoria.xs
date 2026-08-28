table auditoria {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    int? user_id {
      table = "user"
    }
    text acao filters=trim|max:100
    text recurso filters=trim|max:100
    int? registro_id
    text? valor_anterior filters=trim|max:5000
    text? valor_novo filters=trim|max:5000
    text? justificativa filters=trim|max:2000
    text? resultado filters=trim|max:100
    text? endereco_ip filters=trim|max:64
    text? identificador_sessao filters=trim|max:128
    text? rastreamento_id filters=trim|max:128
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "user_id", op: "asc"}]}
    {type: "btree", field: [{name: "recurso", op: "asc"}]}
    {type: "btree", field: [{name: "rastreamento_id", op: "asc"}]}
  ]
  guid = "zUdWeR5DozvmoZf_hl5wUhjtQVE"
}
