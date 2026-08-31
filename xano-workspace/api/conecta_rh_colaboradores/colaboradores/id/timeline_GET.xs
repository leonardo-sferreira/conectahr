// Timeline do colaborador: reune, em ordem cronologica, os eventos de
// historico_profissional (admissao, promocoes, alteracoes, desligamento)
// e as ferias concluidas. Avaliacoes concluidas ainda nao entram porque
// o modulo de avaliacao (secao 6 do plano) nao esta implementado.
// Acesso: RH/ADMIN consultam qualquer colaborador; o proprio colaborador
// consulta a propria timeline; o Gestor consulta colaboradores do
// departamento que ele gerencia (cada gestor gerencia um unico
// departamento).
query "colaboradores/{id}/timeline" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
  }

  stack {
    // Localiza o usuario autenticado.
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

    // Localiza o colaborador alvo da timeline.
    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    // O proprio colaborador (se houver vinculo) pode ver a propria timeline.
    var $e_o_proprio {
      value = ($colaborador_alvo.user_id == $usuario_autenticado.id)
    }

    // Gestor: verifica se o alvo pertence ao departamento que ele gerencia.
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
          if ($departamento_gerenciado != null && $colaborador_alvo.departamento_id == $departamento_gerenciado.id) {
            var.update $e_gestor_da_equipe {
              value = true
            }
          }
        }
      }
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio || $e_gestor_da_equipe) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar esta timeline."
    }

    // Eventos do historico profissional.
    db.query historico_profissional {
      where = $db.historico_profissional.colaborador_id == $colaborador_alvo.id
      sort = {historico_profissional.data_inicio: "asc"}
      return = {type: "list"}
    } as $eventos_historico

    // Ferias concluidas.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_alvo.id && $db.ferias.status == "Concluida"
      sort = {ferias.data_inicio: "asc"}
      return = {type: "list"}
    } as $eventos_ferias
  }

  response = {
    sucesso         : true
    colaborador_id  : $colaborador_alvo.id
    historico       : $eventos_historico
    ferias_concluidas: $eventos_ferias
  }

  guid = "conectahr-colaboradores-timeline-get-0001"
}
