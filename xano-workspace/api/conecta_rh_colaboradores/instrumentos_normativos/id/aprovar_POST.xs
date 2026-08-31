// Aprova (ativa como vigente) um instrumento normativo pendente.
// Bloqueia autoaprovacao: quem aprova nao pode ser quem criou. Para
// instrumentos coletivos (acordo_coletivo, convencao_coletiva,
// termo_aditivo), exige os tres identificadores do Sistema
// Mediador/MTE, data de registro e documento antes de poder ficar
// vigente - sem isso, permanece pendente.
query "instrumentos_normativos/{id}/aprovar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem aprovar instrumentos normativos."
    }

    db.get instrumento_normativo {
      field_name = "id"
      field_value = $input.id
    } as $instrumento_atual

    precondition ($instrumento_atual != null) {
      error_type = "notfound"
      error = "Instrumento normativo nao encontrado."
    }

    precondition ($instrumento_atual.status == "pendente_aprovacao") {
      error_type = "inputerror"
      error = "Somente instrumentos pendentes de aprovacao podem ser aprovados."
    }

    // Bloqueia autoaprovacao.
    precondition ($instrumento_atual.criado_por_user_id != $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Quem criou o instrumento nao pode aprova-lo."
    }

    var $e_instrumento_coletivo {
      value = ($instrumento_atual.tipo == "acordo_coletivo" || $instrumento_atual.tipo == "convencao_coletiva" || $instrumento_atual.tipo == "termo_aditivo")
    }

    // Instrumentos coletivos exigem os tres identificadores, data de
    // registro e documento antes de poderem ficar vigentes.
    precondition ($e_instrumento_coletivo == false || ($instrumento_atual.numero_solicitacao_mediador != null && $instrumento_atual.numero_registro_mte != null && $instrumento_atual.numero_processo_mte != null && $instrumento_atual.data_registro != null && $instrumento_atual.documento_url != null)) {
      error_type = "inputerror"
      error = "Instrumento coletivo sem registro no MTE, data de registro ou documento nao pode ficar vigente."
    }

    db.edit instrumento_normativo {
      field_name = "id"
      field_value = $instrumento_atual.id
      data = {
        status                : "vigente"
        aprovado_por_user_id  : $usuario_autenticado.id
        data_aprovacao          : "now"
        updated_at                 : "now"
      }
    } as $instrumento_aprovado

    // Auditoria: aprovacao de instrumento normativo.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "aprovar_instrumento_normativo"
        recurso    : "instrumento_normativo"
        registro_id: $instrumento_atual.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Instrumento normativo aprovado e vigente."
    instrumento : $instrumento_aprovado
  }

  guid = "conectahr-instrumentos-normativos-aprovar-post-0001"
}
