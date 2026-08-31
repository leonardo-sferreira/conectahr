// RH/ADMIN cria uma regra_override como rascunho, vinculada a um
// instrumento normativo vigente. Bloqueia criacao quando o parametro
// esta marcado como `sem_override` no catalogo de parametros protegidos
// (item 1.10).
query regras_override verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int instrumento_normativo_id
    text parametro filters=trim
    text valor_novo filters=trim|max:500
    int prioridade
    text abrangencia filters=trim
    int? departamento_id?
    int? cargo_id?
    int? colaborador_id?
    text? tipo_contrato? filters=trim|max:20
    text? estado? filters=trim|max:100
    text? municipio? filters=trim|max:120
    text? categoria_profissional? filters=trim|max:200
    date data_inicio
    date? data_fim?
    text? tipo_aplicacao? filters=trim
    text? justificativa? filters=trim|max:2000
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
      error = "Somente RH ou ADMIN podem criar regras de override."
    }

    db.get instrumento_normativo {
      field_name = "id"
      field_value = $input.instrumento_normativo_id
    } as $instrumento

    precondition ($instrumento != null) {
      error_type = "notfound"
      error = "Instrumento normativo nao encontrado."
    }

    precondition ($instrumento.status == "vigente") {
      error_type = "inputerror"
      error = "O instrumento normativo precisa estar vigente para fundamentar um override."
    }

    // Valida o parametro contra o catalogo de parametros protegidos.
    db.query parametro_protegido {
      where = $db.parametro_protegido.parametro == $input.parametro
      return = {type: "single"}
    } as $parametro_catalogo

    precondition ($parametro_catalogo != null) {
      error_type = "inputerror"
      error = "Parametro invalido."
    }

    precondition ($parametro_catalogo.nivel_protecao != "sem_override") {
      error_type = "accessdenied"
      error = "Este parametro nao pode ser sobrescrito por override."
    }

    // Valida a abrangencia usando os valores exatos do Enum.
    precondition ($input.abrangencia == "empresa" || $input.abrangencia == "estabelecimento" || $input.abrangencia == "estado" || $input.abrangencia == "municipio" || $input.abrangencia == "departamento" || $input.abrangencia == "cargo" || $input.abrangencia == "tipo_contrato" || $input.abrangencia == "categoria_profissional" || $input.abrangencia == "colaborador") {
      error_type = "inputerror"
      error = "Abrangencia invalida."
    }

    var $tipo_aplicacao_final {
      value = ($input.tipo_aplicacao != null ? $input.tipo_aplicacao : "futura")
    }

    precondition ($tipo_aplicacao_final == "futura" || $tipo_aplicacao_final == "retroativa") {
      error_type = "inputerror"
      error = "Tipo de aplicacao invalido. Use futura ou retroativa."
    }

    // Aplicacao retroativa exige justificativa (aprovacao especial).
    precondition ($tipo_aplicacao_final != "retroativa" || $input.justificativa != null) {
      error_type = "inputerror"
      error = "Regras retroativas exigem justificativa."
    }

    db.add regra_override {
      data = {
        instrumento_normativo_id  : $instrumento.id
        parametro                    : $input.parametro
        valor_novo                       : $input.valor_novo
        prioridade                          : $input.prioridade
        abrangencia                            : $input.abrangencia
        departamento_id                           : $input.departamento_id
        cargo_id                                     : $input.cargo_id
        colaborador_id                                  : $input.colaborador_id
        tipo_contrato                                      : $input.tipo_contrato
        estado                                                : $input.estado
        municipio                                                : $input.municipio
        categoria_profissional                                      : $input.categoria_profissional
        data_inicio                                                    : $input.data_inicio
        data_fim                                                          : $input.data_fim
        tipo_aplicacao                                                       : $tipo_aplicacao_final
        justificativa                                                           : $input.justificativa
        versao                                                                     : 1
        ativo                                                                         : false
        status                                                                           : "rascunho"
        criado_por_user_id                                                                  : $usuario_autenticado.id
        updated_at                                                                             : "now"
      }
    } as $override_criado

    // Auditoria: criacao de regra de override.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_regra_override"
        recurso    : "regra_override"
        registro_id: $override_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Regra de override criada como rascunho."
    override : $override_criado
  }

  guid = "conectahr-regras-override-post-0001"
}
