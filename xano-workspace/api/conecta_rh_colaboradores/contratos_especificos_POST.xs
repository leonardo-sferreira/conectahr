// RH/ADMIN cria o registro de metadados especificos do contrato de um
// colaborador ESTAGIO, APRENDIZ, TEMPORARIO ou PJ (item 3.6). Nasce como
// "rascunho" — so vira "ativo" apos passar pelas validacoes do tipo em
// contratos_especificos/{id}/ativar.
query contratos_especificos verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int colaborador_id
    text tipo_contrato filters=trim
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh

    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }

    precondition ($perfil_rh == "RH" || $perfil_rh == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem cadastrar contratos especificos."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $tipo_normalizado {
      value = $input.tipo_contrato|trim|to_upper
    }

    precondition ($tipo_normalizado == "ESTAGIO" || $tipo_normalizado == "APRENDIZ" || $tipo_normalizado == "TEMPORARIO" || $tipo_normalizado == "PJ") {
      error_type = "inputerror"
      error = "Tipo de contrato invalido. Use ESTAGIO, APRENDIZ, TEMPORARIO ou PJ."
    }

    // O tipo do modelo contratual precisa bater com o vinculo atual do colaborador.
    precondition ($colaborador_alvo.tipo_contrato == $tipo_normalizado) {
      error_type = "inputerror"
      error = "O tipo informado nao corresponde ao tipo_contrato atual do colaborador."
    }

    // Um colaborador tem no maximo um registro de contrato especifico.
    db.get contrato_especifico {
      field_name = "colaborador_id"
      field_value = $colaborador_alvo.id
    } as $contrato_existente

    precondition ($contrato_existente == null) {
      error_type = "inputerror"
      error = "Este colaborador ja possui um registro de contrato especifico."
    }

    db.add contrato_especifico {
      data = {
        colaborador_id      : $colaborador_alvo.id
        tipo_contrato        : $tipo_normalizado
        status                : "rascunho"
        criado_por_user_id     : $usuario_rh.id
        updated_at               : "now"
      }
    } as $contrato_criado

    db.add auditoria {
      data = {
        user_id    : $usuario_rh.id
        acao       : "criar_contrato_especifico"
        recurso    : "contrato_especifico"
        registro_id: $contrato_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Contrato especifico criado como rascunho. Preencha os campos do tipo e ative pelo endpoint dedicado."
    contrato : $contrato_criado
  }

  guid = "conectahr-contratos-especificos-post-0001"
}
