// Grava na ARP do REP-P o registro tipo 5 (inclusao "I", alteracao "A" ou exclusao "E" de
// empregado; Portaria MTP 671/2021, Anexo IX, item 6.3), com CPF e nome do empregado e o
// CPF de quem fez a operacao. Chamado no cadastro, na mudanca de nome ou CPF e na
// conclusao do desligamento.
function "ConectaHR/registrar_empregado_rep" {
  input {
    int colaborador_id
    text operacao filters=trim|max:1
    int responsavel_user_id
  }

  stack {
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador

    db.get colaborador {
      field_name = "user_id"
      field_value = $input.responsavel_user_id
    } as $ficha_responsavel

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $colaborador.cpf}
    } as $cpf

    function.run "ConectaHR/somente_digitos" {
      input = {texto: ($ficha_responsavel != null ? $ficha_responsavel.cpf : "")}
    } as $cpf_responsavel

    function.run "ConectaHR/gravar_registro_rep" {
      input = {tipo_registro: 5, colaborador_id: $colaborador.id, cpf: $cpf, cpf_responsavel: $cpf_responsavel, responsavel_user_id: $input.responsavel_user_id, dados: {operacao: $input.operacao, nome: $colaborador.nome}}
    } as $registro
  }

  response = $registro

  tags = ["conectahr"]
  guid = "conectahr-registrar-empregado-rep-0001"
}
