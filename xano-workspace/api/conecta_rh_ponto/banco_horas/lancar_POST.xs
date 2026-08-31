// RH/ADMIN registra um lancamento (credito ou debito) no banco de
// horas de um colaborador. Exige que a regra de contrato vigente do
// colaborador permita banco de horas (`regra_contrato.permite_banco_horas`).
// Operacao somente de criacao - o ledger e append-only.
query "banco_horas/lancar" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int colaborador_id
    text tipo filters=trim
    decimal horas filters=min:0.01
    text origem filters=trim|max:200
    int? instrumento_normativo_id?
    date data_lancamento
    date? data_expiracao?
    text? observacao? filters=trim|max:500
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem lancar banco de horas."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Confirma que o tipo de contrato do colaborador permite banco de horas.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colaborador_alvo.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra_do_contrato

    precondition ($regra_do_contrato != null) {
      error_type = "inputerror"
      error = "Nao ha regra de contrato ativa para o tipo de contrato deste colaborador."
    }

    precondition ($regra_do_contrato.permite_banco_horas == true) {
      error_type = "inputerror"
      error = "O tipo de contrato deste colaborador nao permite banco de horas."
    }

    // Valida o tipo do lancamento usando os valores exatos do Enum.
    precondition ($input.tipo == "credito" || $input.tipo == "debito") {
      error_type = "inputerror"
      error = "Tipo invalido. Use credito ou debito."
    }

    db.add banco_horas_lancamento {
      data = {
        colaborador_id        : $colaborador_alvo.id
        tipo                    : $input.tipo
        horas                     : $input.horas
        origem                     : $input.origem
        instrumento_normativo_id     : $input.instrumento_normativo_id
        data_lancamento                : $input.data_lancamento
        data_expiracao                   : $input.data_expiracao
        registrado_por_user_id             : $usuario_autenticado.id
        observacao                           : $input.observacao
        updated_at                             : "now"
      }
    } as $lancamento_criado

    // Auditoria: lancamento de banco de horas.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "lancar_banco_horas"
        recurso       : "banco_horas_lancamento"
        registro_id   : $lancamento_criado.id
        valor_novo    : ($input.tipo ~ ":" ~ ($input.horas|to_text))
        justificativa : $input.origem
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Lancamento registrado com sucesso."
    lancamento  : $lancamento_criado
  }

  guid = "conectahr-banco-horas-lancar-post-0001"
}
