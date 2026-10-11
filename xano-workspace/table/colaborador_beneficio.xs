// Beneficio de uma pessoa (tarefa 82): qual beneficio do catalogo, quanto a empresa paga,
// quanto e descontado do colaborador e a vigencia. Encerrar nao apaga: preenche data_fim e
// desativa, e o historico continua.
table colaborador_beneficio {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int colaborador_id {
      table = "colaborador"
    }

    int beneficio_id {
      table = "beneficio"
    }

    decimal valor_empresa?=0 filters=min:0
    decimal desconto_colaborador?=0 filters=min:0
    date data_inicio
    date? data_fim
    text? observacao filters=trim|max:500
    bool ativo?=true
    int? criado_por_user_id {
      table = "user"
    }

    int? encerrado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-colaborador-beneficio-0001"
}
