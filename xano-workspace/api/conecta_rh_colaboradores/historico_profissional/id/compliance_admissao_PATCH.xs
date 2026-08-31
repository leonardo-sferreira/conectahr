// RH confirma o estado das integracoes eSocial/CTPS Digital para um
// registro de admissao CLT (item 3.5). Integracoes futuras (design.md):
// nao chama servico externo, so registra o estado que o RH confirmou.
query "historico_profissional/{id}/compliance_admissao" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text? esocial_status? filters=trim
    text? ctps_status? filters=trim
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
      error = "Somente RH ou ADMIN podem confirmar o estado de eSocial/CTPS."
    }

    precondition ($input.esocial_status != null || $input.ctps_status != null) {
      error_type = "inputerror"
      error = "Informe esocial_status ou ctps_status."
    }

    db.get historico_profissional {
      field_name = "id"
      field_value = $input.id
    } as $historico_atual

    precondition ($historico_atual != null) {
      error_type = "notfound"
      error = "Registro de historico profissional nao encontrado."
    }

    precondition ($historico_atual.tipo_alteracao == "admissao") {
      error_type = "inputerror"
      error = "So registros de admissao rastreiam eSocial/CTPS."
    }

    precondition ($historico_atual.tipo_contrato == "CLT") {
      error_type = "inputerror"
      error = "So admissoes CLT rastreiam eSocial/CTPS."
    }

    // Normaliza e valida os status informados (mantendo o valor atual quando omitido).
    var $esocial_normalizado {
      value = $historico_atual.esocial_status
    }

    conditional {
      if ($input.esocial_status != null) {
        var.update $esocial_normalizado {
          value = $input.esocial_status|trim|to_lower
        }

        precondition ($esocial_normalizado == "pendente" || $esocial_normalizado == "comunicado" || $esocial_normalizado == "confirmado" || $esocial_normalizado == "indisponivel") {
          error_type = "inputerror"
          error = "esocial_status invalido. Use pendente, comunicado, confirmado ou indisponivel."
        }
      }
    }

    var $ctps_normalizado {
      value = $historico_atual.ctps_status
    }

    conditional {
      if ($input.ctps_status != null) {
        var.update $ctps_normalizado {
          value = $input.ctps_status|trim|to_lower
        }

        precondition ($ctps_normalizado == "pendente" || $ctps_normalizado == "comunicado" || $ctps_normalizado == "confirmado" || $ctps_normalizado == "indisponivel") {
          error_type = "inputerror"
          error = "ctps_status invalido. Use pendente, comunicado, confirmado ou indisponivel."
        }
      }
    }

    db.edit historico_profissional {
      field_name = "id"
      field_value = $historico_atual.id
      data = {
        esocial_status: $esocial_normalizado
        ctps_status   : $ctps_normalizado
        updated_at    : "now"
      }
    } as $historico_atualizado

    // Auditoria: confirmacao de estado eSocial/CTPS.
    db.add auditoria {
      data = {
        user_id       : $usuario_rh.id
        acao          : "confirmar_compliance_admissao"
        recurso       : "historico_profissional"
        registro_id   : $historico_atual.id
        valor_anterior: ("esocial=" ~ ($historico_atual.esocial_status != null ? $historico_atual.esocial_status : "null") ~ "; ctps=" ~ ($historico_atual.ctps_status != null ? $historico_atual.ctps_status : "null"))
        valor_novo    : ("esocial=" ~ ($esocial_normalizado != null ? $esocial_normalizado : "null") ~ "; ctps=" ~ ($ctps_normalizado != null ? $ctps_normalizado : "null"))
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Estado de eSocial/CTPS atualizado com sucesso."
    historico: $historico_atualizado
  }

  guid = "conectahr-historico-profissional-compliance-admissao-0001"
}
