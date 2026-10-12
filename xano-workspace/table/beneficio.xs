// Catalogo de beneficios da empresa (tarefa 82). O RH cadastra; o vinculo com cada pessoa
// fica em colaborador_beneficio, com valor, desconto e vigencia. Desde a tarefa 85, o catalogo guarda o valor
// e o desconto padrao, que "alterar para todos" aplica a quem tem o beneficio.
table beneficio {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    text nome filters=trim|min:2|max:100
    enum tipo {
      values = ["vale_refeicao", "vale_alimentacao", "vale_transporte", "plano_saude", "plano_odontologico", "seguro_vida", "auxilio_home_office", "auxilio_creche", "outro"]
    }

    text? operadora filters=trim|max:100
    text? descricao filters=trim|max:500
    decimal valor_empresa_padrao?=0 filters=min:0
    decimal desconto_padrao?=0 filters=min:0
    bool ativo?=true
    int? criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "nome", op: "asc"}]}
  ]

  guid = "conectahr-beneficio-0001"
}
