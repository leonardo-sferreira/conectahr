// RH/ADMIN inicia o onboarding de um colaborador: cria o checklist com
// os itens do Requirement "Onboarding de colaborador" (dados pessoais,
// acesso, troca de senha, documentos obrigatorios, aprovacoes, gestor,
// departamento, contrato, jornada, metas iniciais e acompanhamentos de
// 30/60/90 dias), cada um com seu responsavel (rh, colaborador ou
// gestor). Um colaborador so pode ter um onboarding.
query "colaboradores/{id}/onboarding" verb=POST {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem iniciar onboarding."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $status_colaborador {
      value = $colaborador_alvo.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel iniciar onboarding para colaborador desligado."
    }

    db.query onboarding {
      where = $db.onboarding.colaborador_id == $colaborador_alvo.id
      return = {type: "single"}
    } as $onboarding_existente

    precondition ($onboarding_existente == null) {
      error_type = "inputerror"
      error = "Este colaborador ja possui um onboarding iniciado."
    }

    db.transaction {
      stack {
        db.add onboarding {
          data = {
            colaborador_id       : $colaborador_alvo.id
            iniciado_por_user_id : $usuario_autenticado.id
            data_inicio            : "now"
            status                  : "em_andamento"
            updated_at               : "now"
          }
        } as $onboarding_criado

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "dados_pessoais", descricao: "Conferir dados pessoais do colaborador.", responsavel: "rh", updated_at: "now"}
        } as $item1

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "acesso", descricao: "Criar a conta de acesso do colaborador.", responsavel: "rh", updated_at: "now"}
        } as $item2

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "troca_senha", descricao: "Trocar a senha temporaria no primeiro acesso.", responsavel: "colaborador", updated_at: "now"}
        } as $item3

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "documentos_obrigatorios", descricao: "Enviar os documentos obrigatorios de admissao.", responsavel: "colaborador", updated_at: "now"}
        } as $item4

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "aprovacoes", descricao: "Aprovar os documentos enviados.", responsavel: "rh", updated_at: "now"}
        } as $item5

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "gestor", descricao: "Confirmar o gestor responsavel pelo colaborador.", responsavel: "rh", updated_at: "now"}
        } as $item6

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "departamento", descricao: "Confirmar o departamento do colaborador.", responsavel: "rh", updated_at: "now"}
        } as $item7

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "contrato", descricao: "Confirmar o tipo de contrato e condicoes contratuais.", responsavel: "rh", updated_at: "now"}
        } as $item8

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "jornada", descricao: "Confirmar a jornada aplicavel ao contrato.", responsavel: "rh", updated_at: "now"}
        } as $item9

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "metas_iniciais", descricao: "Definir metas iniciais com o colaborador.", responsavel: "gestor", updated_at: "now"}
        } as $item10

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "acompanhamento_30_dias", descricao: "Realizar acompanhamento de 30 dias.", responsavel: "gestor", updated_at: "now"}
        } as $item11

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "acompanhamento_60_dias", descricao: "Realizar acompanhamento de 60 dias.", responsavel: "gestor", updated_at: "now"}
        } as $item12

        db.add onboarding_item {
          data = {onboarding_id: $onboarding_criado.id, categoria: "acompanhamento_90_dias", descricao: "Realizar acompanhamento de 90 dias.", responsavel: "gestor", updated_at: "now"}
        } as $item13

        db.add auditoria {
          data = {
            user_id    : $usuario_autenticado.id
            acao       : "iniciar_onboarding"
            recurso    : "onboarding"
            registro_id: $onboarding_criado.id
            resultado  : "sucesso"
          }
        } as $evento_auditoria
      }
    }

    db.query onboarding_item {
      where = $db.onboarding_item.onboarding_id == $onboarding_criado.id
      return = {type: "list"}
    } as $itens_criados
  }

  response = {
    sucesso   : true
    mensagem  : "Onboarding iniciado com sucesso."
    onboarding: $onboarding_criado
    itens     : $itens_criados
  }

  guid = "conectahr-colaboradores-onboarding-post-0001"
}
