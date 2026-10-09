// Lista a equipe do Gestor autenticado: os colaboradores nao desligados do
// departamento que ele gerencia. So para Gestor. Devolve apenas dados de
// trabalho (nome, cargo, departamento, nivel, contrato, admissao e status); nunca
// CPF, salario, dados bancarios, contato, endereco nem data de nascimento.
// `colaboradores/{id}` continua restrito a RH e Admin.
query minha_equipe verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "GESTOR") {
      error_type = "accessdenied"
      error = "Somente o Gestor pode consultar a propria equipe."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_do_gestor

    var $departamento_id {
      value = null
    }

    var $equipe {
      value = []
    }

    conditional {
      if ($colaborador_do_gestor != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_do_gestor.id
          return = {type: "single"}
        } as $departamento_gerenciado

        conditional {
          if ($departamento_gerenciado != null) {
            var.update $departamento_id {
              value = $departamento_gerenciado.id
            }

            db.query colaborador {
              where = $db.colaborador.departamento_id == $departamento_gerenciado.id && $db.colaborador.status != "Desligado"
              sort = {colaborador.nome: "asc"}
              return = {type: "list"}
              output = ["id", "nome", "cargo_id", "departamento_id", "nivel", "tipo_contrato", "data_admissao", "status"]
            } as $equipe_consulta

            var $hoje_equipe {
              value = now|format_timestamp:"Y-m-d":"UTC"
            }

            foreach ($equipe_consulta) {
              each as $membro {
                // Ferias aprovadas em andamento ou proximas (so o periodo).
                db.query ferias {
                  where = $db.ferias.colaborador_id == $membro.id && $db.ferias.status == "Aprovada" && $db.ferias.data_fim >= $hoje_equipe
                  sort = {ferias.data_inicio: "asc"}
                  return = {type: "list"}
                  output = ["data_inicio", "data_fim", "status"]
                } as $ferias_do_membro

                // Ausencias aprovadas ou registradas em andamento ou proximas: so tipo,
                // periodo e status (nunca motivo, observacao nem comprovante).
                db.query ausencia {
                  where = $db.ausencia.colaborador_id == $membro.id && $db.ausencia.data_fim >= $hoje_equipe
                  sort = {ausencia.data_inicio: "asc"}
                  return = {type: "list"}
                  output = ["tipo", "data_inicio", "data_fim", "status"]
                } as $ausencias_do_membro

                var $ausencias_visiveis {
                  value = []
                }

                foreach ($ausencias_do_membro) {
                  each as $ausencia_item {
                    conditional {
                      if ($ausencia_item.status == "Aprovada" || $ausencia_item.status == "Registrado") {
                        var.update $ausencias_visiveis {
                          value = $ausencias_visiveis|push:$ausencia_item
                        }
                      }
                    }
                  }
                }

                db.query registro_ponto {
                  where = $db.registro_ponto.colaborador_id == $membro.id && $db.registro_ponto.data == $hoje_equipe
                  return = {type: "single"}
                  output = ["status"]
                } as $ponto_do_membro

                var.update $equipe {
                  value = $equipe|push:{
                    id             : $membro.id
                    nome           : $membro.nome
                    cargo_id       : $membro.cargo_id
                    departamento_id: $membro.departamento_id
                    nivel          : $membro.nivel
                    tipo_contrato  : $membro.tipo_contrato
                    data_admissao  : $membro.data_admissao
                    status         : $membro.status
                    ferias_proximas: $ferias_do_membro
                    ausencias      : $ausencias_visiveis
                    ponto_hoje     : ($ponto_do_membro != null ? $ponto_do_membro.status : null)
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso        : true
    departamento_id: $departamento_id
    total          : ($equipe|count)
    equipe         : $equipe
  }

  guid = "conectahr-minha-equipe-get-0001"
}
