table comunicado {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    text titulo filters=trim|min:3|max:200
    text conteudo filters=trim|min:5|max:5000
    enum publico_alvo {
      values = ["todos", "departamento", "perfil"]
    }
    int? departamento_id {
      table = "departamento"
    }
    enum? perfil_alvo {
      values = ["Admin", "RH", "Colaborador", "Gestor"]
    }
    date data_inicio
    date? data_fim
    int publicado_por_user_id {
      table = "user"
    }
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]

  guid = "conectahr-comunicado-0001"
}
