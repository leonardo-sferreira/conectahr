table instrumento_normativo {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    enum tipo {
      values = ["acordo_coletivo", "convencao_coletiva", "termo_aditivo", "regime_especial", "norma_legal", "decisao_judicial", "acordo_individual_autorizado"]
    }
    text titulo filters=trim|min:2|max:200
    text descricao filters=trim|max:2000
    text entidade_responsavel filters=trim|max:200
    text categoria_profissional filters=trim|max:200
    text abrangencia_territorial filters=trim|max:500
    text numero_solicitacao_mediador? filters=trim|max:20
    text numero_registro_mte? filters=trim|max:20
    text numero_processo_mte? filters=trim|max:30
    date? data_registro
    date data_inicio
    date? data_fim
    text documento_url filters=trim|max:500
    text hash_documento filters=trim|max:128
    text? observacao filters=trim|max:1000
    enum status?=rascunho {
      values = ["rascunho", "pendente_aprovacao", "vigente", "suspenso", "expirado", "revogado", "rejeitado"]
    }
    int criado_por_user_id {
      table = "user"
    }
    int? aprovado_por_user_id {
      table = "user"
    }
    timestamp? data_aprovacao
    int? instrumento_principal_id {
      table = "instrumento_normativo"
    }
    text? clausulas_alteradas filters=trim|max:2000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
    {type: "btree", field: [{name: "tipo", op: "asc"}]}
    {type: "btree", field: [{name: "data_inicio", op: "desc"}]}
    {type: "btree", field: [{name: "data_fim", op: "asc"}]}
  ]
  guid = "3dGjNyPNwcLdH9wgs1dFkEarDr0"
}
