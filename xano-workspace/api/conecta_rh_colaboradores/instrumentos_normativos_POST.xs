// RH/ADMIN cadastra um instrumento normativo como rascunho.
query instrumentos_normativos verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text tipo filters=trim
    text titulo filters=trim|min:2|max:200
    text descricao filters=trim|max:2000
    text entidade_responsavel filters=trim|max:200
    text categoria_profissional filters=trim|max:200
    text abrangencia_territorial filters=trim|max:500
    text? numero_solicitacao_mediador? filters=trim|max:20
    text? numero_registro_mte? filters=trim|max:20
    text? numero_processo_mte? filters=trim|max:30
    date? data_registro?
    date data_inicio
    date? data_fim?
    text documento_url filters=trim|max:500
    text hash_documento filters=trim|max:128
    text? observacao? filters=trim|max:1000
    int? instrumento_principal_id?
    text? clausulas_alteradas? filters=trim|max:2000
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
      error = "Somente RH ou ADMIN podem cadastrar instrumentos normativos."
    }

    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo == "acordo_coletivo" || $input.tipo == "convencao_coletiva" || $input.tipo == "termo_aditivo" || $input.tipo == "regime_especial" || $input.tipo == "norma_legal" || $input.tipo == "decisao_judicial" || $input.tipo == "acordo_individual_autorizado") {
      error_type = "inputerror"
      error = "Tipo de instrumento invalido."
    }

    // Valida o formato dos identificadores do Sistema Mediador/MTE
    // quando informados (item 4.16) — sem regex, ver validar_formato_mte.
    conditional {
      if ($input.numero_solicitacao_mediador != null) {
        function.run "ConectaHR/validar_formato_mte" {
          input = {valor: $input.numero_solicitacao_mediador, tipo: "mediador"}
        } as $formato_mediador

        precondition ($formato_mediador.valido) {
          error_type = "inputerror"
          error = $formato_mediador.motivo
        }
      }
    }

    conditional {
      if ($input.numero_registro_mte != null) {
        function.run "ConectaHR/validar_formato_mte" {
          input = {valor: $input.numero_registro_mte, tipo: "registro_mte"}
        } as $formato_registro

        precondition ($formato_registro.valido) {
          error_type = "inputerror"
          error = $formato_registro.motivo
        }
      }
    }

    conditional {
      if ($input.numero_processo_mte != null) {
        function.run "ConectaHR/validar_formato_mte" {
          input = {valor: $input.numero_processo_mte, tipo: "processo_mte"}
        } as $formato_processo

        precondition ($formato_processo.valido) {
          error_type = "inputerror"
          error = $formato_processo.motivo
        }
      }
    }

    db.add instrumento_normativo {
      data = {
        tipo                        : $input.tipo
        titulo                        : $input.titulo
        descricao                        : $input.descricao
        entidade_responsavel                 : $input.entidade_responsavel
        categoria_profissional                  : $input.categoria_profissional
        abrangencia_territorial                    : $input.abrangencia_territorial
        numero_solicitacao_mediador                   : $input.numero_solicitacao_mediador
        numero_registro_mte                              : $input.numero_registro_mte
        numero_processo_mte                                 : $input.numero_processo_mte
        data_registro                                          : $input.data_registro
        data_inicio                                               : $input.data_inicio
        data_fim                                                     : $input.data_fim
        documento_url                                                   : $input.documento_url
        hash_documento                                                     : $input.hash_documento
        observacao                                                            : $input.observacao
        status                                                                   : "rascunho"
        criado_por_user_id                                                          : $usuario_autenticado.id
        instrumento_principal_id                                                       : $input.instrumento_principal_id
        clausulas_alteradas                                                               : $input.clausulas_alteradas
        updated_at                                                                           : "now"
      }
    } as $instrumento_criado

    // Auditoria: cadastro de instrumento normativo.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "cadastrar_instrumento_normativo"
        recurso    : "instrumento_normativo"
        registro_id: $instrumento_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Instrumento normativo cadastrado como rascunho."
    instrumento : $instrumento_criado
  }

  guid = "conectahr-instrumentos-normativos-post-0001"
}
