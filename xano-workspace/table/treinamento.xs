// Catalogo de treinamentos (change treinamentos-obrigatorios, D1): os obrigatorios por lei (NRs, a
// orientacao anual sobre assedio da Lei 14.457/2022), de compliance e de desenvolvimento. validade_meses = 0
// significa sem validade (vale uma vez). publico: todos ou so os departamentos de departamento_ids (",1,4,").
table treinamento {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    text nome filters=trim|max:200
    text? descricao filters=trim|max:1000
    enum categoria {
      values = ["legal", "seguranca", "compliance", "integracao", "desenvolvimento"]
    }

    int carga_horas?=0
    int validade_meses?=0
    bool obrigatorio?=true
    enum publico?=todos {
      values = ["todos", "departamentos"]
    }

    text? departamento_ids filters=trim|max:500
    bool ativo?=true
    int criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
  ]

  guid = "conectahr-treinamento-0001"
}
