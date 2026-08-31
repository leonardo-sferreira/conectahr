// Envia reconhecimento/feedback a um colaborador. A visibilidade nao e
// escolhida pelo remetente: e determinada pela relacao com o
// destinatario (decisao registrada em design.md). Quando o remetente e
// o Gestor do departamento do destinatario, o registro e privado e
// pode conter conteudo corretivo. Quando e um colega, o registro e
// publico e deve conter apenas reconhecimento positivo (moderado a
// posteriori por RH/ADMIN via `reconhecimentos/{id}/moderar`).
query reconhecimentos verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int destinatario_colaborador_id
    int competencia_avaliacao_id
    text titulo filters=trim|max:100
    text mensagem filters=trim|max:1500
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

    db.get colaborador {
      field_name = "id"
      field_value = $input.destinatario_colaborador_id
    } as $destinatario

    precondition ($destinatario != null) {
      error_type = "notfound"
      error = "Colaborador destinatario nao encontrado."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_remetente

    // Impede enviar reconhecimento para si mesmo.
    precondition ($colaborador_remetente == null || $colaborador_remetente.id != $destinatario.id) {
      error_type = "inputerror"
      error = "Nao e possivel enviar reconhecimento para si mesmo."
    }

    db.get competencia_avaliacao {
      field_name = "id"
      field_value = $input.competencia_avaliacao_id
    } as $competencia

    precondition ($competencia != null) {
      error_type = "notfound"
      error = "Competencia nao encontrada."
    }

    // Determina se o remetente e o Gestor do departamento do destinatario.
    var $e_gestor_do_destinatario {
      value = false
    }

    conditional {
      if ($colaborador_remetente != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_remetente.id
          return = {type: "single"}
        } as $departamento_gerenciado

        conditional {
          if ($departamento_gerenciado != null && $destinatario.departamento_id == $departamento_gerenciado.id) {
            var.update $e_gestor_do_destinatario {
              value = true
            }
          }
        }
      }
    }

    var $visibilidade_final {
      value = ($e_gestor_do_destinatario ? "privado" : "publico")
    }

    db.add reconhecimento {
      data = {
        remetente_user_id            : $usuario_autenticado.id
        destinatario_colaborador_id    : $destinatario.id
        competencia_avaliacao_id         : $competencia.id
        titulo                              : $input.titulo
        mensagem                              : $input.mensagem
        visibilidade                            : $visibilidade_final
        status                                    : "ativo"
        updated_at                                  : "now"
      }
    } as $reconhecimento_criado
  }

  response = {
    sucesso        : true
    mensagem       : "Reconhecimento enviado com sucesso."
    reconhecimento : $reconhecimento_criado
  }

  guid = "conectahr-reconhecimentos-post-0001"
}
