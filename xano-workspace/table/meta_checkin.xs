// Trilha completa de check-ins de uma meta (append-only). A meta_avaliacao
// guarda so o check-in mais recente para consulta rapida; este historico
// preserva todos, inclusive alteracoes de prazo.
table meta_checkin {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    int meta_avaliacao_id {
      table = "meta_avaliacao"
    }
    int registrado_por_user_id {
      table = "user"
    }
    decimal progresso_percentual filters=min:0|max:100
    text? comentario filters=trim|max:2000
    text? dificuldades filters=trim|max:2000
    text? evidencia filters=trim|max:1000
    date? novo_prazo
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "meta_avaliacao_id", op: "asc"}]}
  ]

  guid = "conectahr-meta-checkin-0001"
}
