table artigo_faq {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    enum categoria {
      values = ["ferias", "ponto", "documentos", "politicas_internas"]
    }
    text titulo filters=trim|max:200
    text conteudo filters=trim|max:5000
    int publicado_por_user_id {
      table = "user"
    }
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "categoria", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]

  guid = "conectahr-artigo-faq-0001"
}
