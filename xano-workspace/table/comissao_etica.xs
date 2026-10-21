// Membros da comissao de etica, os unicos que veem e apuram as denuncias (change
// canal-de-denuncias, D2). O Admin inclui e remove; remover so desativa (historico).
// Ser Admin ou RH nao da acesso a fila: so ser membro ativo.
table comissao_etica {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int user_id {
      table = "user"
    }

    int incluido_por_user_id {
      table = "user"
    }

    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "user_id", op: "asc"}]}
  ]

  guid = "conectahr-comissao-etica-0001"
}
