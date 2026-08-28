table colaborador {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    int? user_id {
      table = "user"
    }
  
    text nome filters=trim|min:2|max:120
    email email_pessoal filters=trim|lower
    text cpf filters=trim|max:11|min:11
    enum nivel {
      values = ["l1", "l2", "l3", "l4", "l5"]
    }
  
    date? nivel_desde?
    date? data_nascimento
    text telefone filters=trim
    text cep? filters=trim
    text logradouro filters=trim
    text numero filters=trim
    text complemento? filters=trim
    text bairro filters=trim
    text cidade? filters=trim
    text estado? filters=trim
    date? data_admissao
    date? data_desligamento?
    int cargo_id {
      table = "cargo"
    }
  
    int departamento_id {
      table = "departamento"
    }
  
    enum tipo_contrato {
      values = ["CLT", "PJ", "ESTAGIO", "APRENDIZ", "TEMPORARIO", "OUTRO"]
    }
  
    decimal salario
    decimal carga_horaria_semanal
    enum status {
      values = ["Ativo", "Ferias", "Afastado", "Desligado"]
    }
  
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "cpf", op: "asc"}]}
    {type: "btree|unique", field: [{name: "user_id", op: "asc"}]}
    {type: "btree", field: [{name: "cargo_id", op: "asc"}]}
    {
      type : "btree"
      field: [{name: "departamento_id", op: "asc"}]
    }
  ]

  guid = "DsS0x6ZG9UkTiJU75fCi6I5B7jM"
}