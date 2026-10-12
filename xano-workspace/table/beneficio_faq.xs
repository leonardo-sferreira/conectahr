// Perguntas e respostas de um beneficio (tarefa 85): o que e, como usar etc. O RH mantem;
// o colaborador ve as do beneficio que tem. Remover desativa, sem apagar.
table beneficio_faq {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int beneficio_id {
      table = "beneficio"
    }

    text pergunta filters=trim|min:3|max:200
    text resposta filters=trim|min:3|max:2000
    int ordem?=0
    bool ativo?=true
    int? criado_por_user_id {
      table = "user"
    }

    int? atualizado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "beneficio_id", op: "asc"}]}
  ]

  guid = "conectahr-beneficio-faq-0001"
}
