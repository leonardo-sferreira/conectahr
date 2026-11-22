table reuniao_individual {
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
    int gestor_user_id {
      table = "user"
    }
    date data_reuniao
    text assuntos filters=trim|max:2000
    text? acordos filters=trim|max:2000
    text? acoes filters=trim|max:2000
    int? responsavel_acoes_user_id {
      table = "user"
    }
    date? prazo_acoes
    date? proxima_reuniao
    enum visibilidade?=privado {
      values = ["privado", "compartilhado_rh"]
    }

    // Agenda simples da 1:1 (concluir-metas-pdi-equipe, D4). Sem situacao: registro antigo, ja realizado.
    text? hora? filters=trim|max:5
    enum? situacao? {
      values = ["agendada", "realizada", "cancelada"]
    }

    timestamp? situacao_em?
    text? motivo_cancelamento? filters=trim|max:500
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "gestor_user_id", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-reuniao-individual-0001"
}
