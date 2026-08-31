// Rejeita uma correcao de ponto, com justificativa. Nao altera o
// registro de ponto. Responsavel autorizado: RH, ADMIN, ou o Gestor do
// departamento do colaborador.
query "correcoes_ponto/{id}/rejeitar" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int id
    text motivo_decisao filters=trim|min:5|max:1000
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

    db.get correcao_ponto {
      field_name = "id"
      field_value = $input.id
    } as $correcao_atual

    precondition ($correcao_atual != null) {
      error_type = "notfound"
      error = "Solicitacao de correcao nao encontrada."
    }

    precondition ($correcao_atual.status == "pendente") {
      error_type = "inputerror"
      error = "Somente solicitacoes pendentes podem ser rejeitadas."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $correcao_atual.colaborador_id
    } as $colaborador_da_correcao

    precondition ($colaborador_da_correcao != null) {
      error_type = "notfound"
      error = "Colaborador relacionado a correcao nao encontrado."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $e_gestor_da_equipe {
      value = false
    }

    conditional {
      if ($perfil_autenticado == "GESTOR" && $colaborador_autenticado != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $departamento_gerenciado

        conditional {
          if ($departamento_gerenciado != null && $colaborador_da_correcao.departamento_id == $departamento_gerenciado.id) {
            var.update $e_gestor_da_equipe {
              value = true
            }
          }
        }
      }
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_gestor_da_equipe) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para decidir esta correcao de ponto."
    }

    db.edit correcao_ponto {
      field_name = "id"
      field_value = $correcao_atual.id
      data = {
        status                : "rejeitada"
        decidido_por_user_id  : $usuario_autenticado.id
        motivo_decisao          : $input.motivo_decisao
        data_decisao             : "now"
        updated_at                : "now"
      }
    } as $correcao_rejeitada

    // Auditoria: rejeicao de correcao de ponto.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "rejeitar_correcao_ponto"
        recurso       : "correcao_ponto"
        registro_id   : $correcao_atual.id
        justificativa : $input.motivo_decisao
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Correcao de ponto rejeitada."
    correcao: $correcao_rejeitada
  }

  guid = "conectahr-correcoes-ponto-rejeitar-post-0001"
}
