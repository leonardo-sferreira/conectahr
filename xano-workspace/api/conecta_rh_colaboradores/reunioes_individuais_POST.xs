// Gestor registra uma reuniao individual (1:1) com um colaborador da
// propria equipe. Por padrao e privada (so gestor e colaborador);
// pode ser marcada como compartilhada com RH quando necessario.
query reunioes_individuais verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int colaborador_id
    date data_reuniao
    text assuntos filters=trim|max:2000
    text? acordos? filters=trim|max:2000
    text? acoes? filters=trim|max:2000
    int? responsavel_acoes_user_id?
    date? prazo_acoes?
    date? proxima_reuniao?
    text? visibilidade? filters=trim
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

    precondition ($perfil_autenticado == "GESTOR" || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente Gestor, RH ou ADMIN podem registrar reunioes individuais."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Gestor so pode registrar com colaboradores do proprio departamento.
    conditional {
      if ($perfil_autenticado == "GESTOR") {
        db.get colaborador {
          field_name = "user_id"
          field_value = $usuario_autenticado.id
        } as $colaborador_gestor

        precondition ($colaborador_gestor != null) {
          error_type = "notfound"
          error = "Nao existe um colaborador vinculado a esta conta."
        }

        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_gestor.id
          return = {type: "single"}
        } as $departamento_gerenciado

        precondition ($departamento_gerenciado != null && $colaborador_alvo.departamento_id == $departamento_gerenciado.id) {
          error_type = "accessdenied"
          error = "Voce so pode registrar reunioes com colaboradores da propria equipe."
        }
      }
    }

    var $visibilidade_normalizada {
      value = "privado"
    }

    conditional {
      if ($input.visibilidade != null) {
        var.update $visibilidade_normalizada {
          value = $input.visibilidade|trim|to_lower
        }

        precondition ($visibilidade_normalizada == "privado" || $visibilidade_normalizada == "compartilhado_rh") {
          error_type = "inputerror"
          error = "Visibilidade invalida. Use privado ou compartilhado_rh."
        }
      }
    }

    db.add reuniao_individual {
      data = {
        colaborador_id             : $colaborador_alvo.id
        gestor_user_id                : $usuario_autenticado.id
        data_reuniao                     : $input.data_reuniao
        assuntos                            : $input.assuntos
        acordos                                : $input.acordos
        acoes                                     : $input.acoes
        responsavel_acoes_user_id                   : $input.responsavel_acoes_user_id
        prazo_acoes                                    : $input.prazo_acoes
        proxima_reuniao                                   : $input.proxima_reuniao
        visibilidade                                         : $visibilidade_normalizada
        updated_at                                              : "now"
      }
    } as $reuniao_criada
  }

  response = {
    sucesso : true
    mensagem: "Reuniao registrada com sucesso."
    reuniao : $reuniao_criada
  }

  guid = "conectahr-reunioes-individuais-post-0001"
}
