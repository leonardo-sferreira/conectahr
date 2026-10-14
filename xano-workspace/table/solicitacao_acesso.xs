// Pedido do RH para o Admin trocar o perfil de acesso de uma conta (change pedido-de-acesso).
// O RH escolhe o perfil e justifica; o Admin aprova (o perfil e trocado na hora) ou recusa com motivo.
table solicitacao_acesso {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int usuario_id {
      table = "user"
    }

    int colaborador_id? {
      table = "colaborador"
    }

    int solicitante_user_id {
      table = "user"
    }

    enum perfil_atual {
      values = ["Admin", "RH", "Gestor", "Colaborador"]
    }

    enum perfil_solicitado {
      values = ["Admin", "RH", "Gestor", "Colaborador"]
    }

    text justificativa filters=trim|max:1000
    enum status?=pendente {
      values = ["pendente", "aprovada", "recusada"]
    }

    int decidido_por_user_id? {
      table = "user"
    }

    timestamp? data_decisao?
    text? motivo_decisao filters=trim|max:1000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "usuario_id", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]
  guid = "8_hCzSwO0ZW7NxTg90DMHAJT9-0"
}
