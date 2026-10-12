// Configuracoes do sistema decididas pelo RH (tarefa 83). Uma linha por chave.
// prazo_correcao_ponto_dias: quantos dias para tras o colaborador pode pedir correcao de
// ponto; sem linha (ou valor nulo), sem limite.
table configuracao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    text chave filters=trim|max:80
    int? valor_inteiro
    int? atualizado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "chave", op: "asc"}]}
  ]

  guid = "conectahr-configuracao-0001"
}
