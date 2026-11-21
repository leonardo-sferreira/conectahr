// Timeline do colaborador: reune, em ordem cronologica, os eventos de
// historico_profissional (admissao, promocoes, alteracoes, desligamento)
// e as ferias concluidas. Avaliacoes concluidas ainda nao entram porque
// o modulo de avaliacao (secao 6 do plano) nao esta implementado.
// Acesso: RH/ADMIN consultam qualquer colaborador; o proprio colaborador
// consulta a propria timeline; o Gestor consulta colaboradores do
// departamento que ele gerencia (cada gestor gerencia um unico
// departamento).
// Campos por perfil (LGPD, minimizacao; 21/11/2026): RH e Admin recebem o
// historico com salario, motivo e as situacoes de eSocial e CTPS; o Gestor e a
// propria pessoa recebem so tipo, datas, cargo, departamento, nivel, contrato e
// jornada. Ferias saem so com periodo e dias, sem as observacoes.
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

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
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

    var $ve_tudo {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")
    }

    var $historico_resposta {
      value = []
    }

    foreach ($eventos_historico) {
      each as $h {
        var $linha_historico {
          value = {id: $h.id, tipo_alteracao: $h.tipo_alteracao, data_inicio: $h.data_inicio, data_fim: $h.data_fim, cargo_id: $h.cargo_id, departamento_id: $h.departamento_id, nivel: $h.nivel, tipo_contrato: $h.tipo_contrato, carga_horaria_semanal: $h.carga_horaria_semanal}
        }

        conditional {
          if ($ve_tudo) {
            var.update $linha_historico {
              value = $linha_historico|set:"salario":$h.salario|set:"motivo_alteracao":$h.motivo_alteracao|set:"esocial_status":$h.esocial_status|set:"ctps_status":$h.ctps_status
            }
          }
        }

        var.update $historico_resposta {
          value = $historico_resposta|push:$linha_historico
        }
      }
    }

    var $ferias_resposta {
      value = []
    }

    foreach ($eventos_ferias) {
      each as $f {
        var.update $ferias_resposta {
          value = $ferias_resposta|push:{id: $f.id, data_inicio: $f.data_inicio, data_fim: $f.data_fim, quantidade_dias: $f.quantidade_dias}
        }
      }
    }
  }

  response = {
    sucesso         : true
    colaborador_id  : $colaborador_alvo.id
    historico       : $historico_resposta
    ferias_concluidas: $ferias_resposta
  }

  guid = "conectahr-colaboradores-timeline-get-0001"
}
