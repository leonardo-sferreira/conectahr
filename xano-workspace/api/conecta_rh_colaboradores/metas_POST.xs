// Colaborador cria uma meta anual em um ciclo. RH/ADMIN podem criar em
// nome de qualquer colaborador; o Gestor, so para os liderados diretos e para o
// departamento de que e gestor (concluir-metas-pdi-equipe, D2). Meta criada para
// outra pessoa avisa no sino e por e-mail (D5) e vai para a auditoria.
query metas verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int? colaborador_id?
    int ciclo_avaliacao_id
    text titulo filters=trim|max:500
    text descricao filters=trim|max:500
    text indicador filters=trim|max:300
    decimal? valor_esperado?
    text? unidade_medida? filters=trim|max:50
    decimal peso filters=max:100
    date? data_prazo?
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    // Define o colaborador-alvo: o proprio autenticado, ou outro quando
    // RH/ADMIN/Gestor informar.
    var $colaborador_alvo_id {
      value = null
    }

    conditional {
      if ($input.colaborador_id == null || $input.colaborador_id == $colaborador_autenticado.id) {
        precondition ($colaborador_autenticado != null) {
          error_type = "notfound"
          error = "Nao existe um colaborador vinculado a esta conta."
        }

        var.update $colaborador_alvo_id {
          value = $colaborador_autenticado.id
        }
      }
    }

    conditional {
      if ($input.colaborador_id != null && $colaborador_autenticado != null && $input.colaborador_id != $colaborador_autenticado.id) {
        precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR") {
          error_type = "accessdenied"
          error = "Somente RH, ADMIN ou Gestor podem criar metas para outro colaborador."
        }

        var.update $colaborador_alvo_id {
          value = $input.colaborador_id
        }
      }
    }

    conditional {
      if ($input.colaborador_id != null && $colaborador_autenticado == null) {
        precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR") {
          error_type = "accessdenied"
          error = "Somente RH, ADMIN ou Gestor podem criar metas para outro colaborador."
        }

        var.update $colaborador_alvo_id {
          value = $input.colaborador_id
        }
      }
    }

    db.get colaborador {
      field_name = "id"
      field_value = $colaborador_alvo_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Lideranca (decisoes D1 a D4 de concluir-metas-pdi-equipe): liderado direto e a ficha cujo superior e a ficha do
    // autenticado; o departamento conta quando o autenticado e o gestor dele.
    var $id_ficha_autenticada {
      value = ($colaborador_autenticado == null) ? 0 : $colaborador_autenticado.id
    }

    var $e_liderado_direto {
      value = ($colaborador_alvo.superior_colaborador_id != null) && ($colaborador_alvo.superior_colaborador_id == $id_ficha_autenticada) && ($colaborador_alvo.status != "Desligado")
    }

    db.get departamento {
      field_name = "id"
      field_value = $colaborador_alvo.departamento_id
    } as $departamento_alvo

    var $gestor_do_departamento_alvo {
      value = (($departamento_alvo == null) || ($departamento_alvo.ativo == false)) ? 0 : $departamento_alvo.gestor_colaborador_id
    }

    var $e_do_meu_departamento {
      value = ($gestor_do_departamento_alvo != null) && ($gestor_do_departamento_alvo == $id_ficha_autenticada) && ($id_ficha_autenticada != 0) && ($colaborador_alvo.status != "Desligado")
    }

    var $e_para_si {
      value = ($colaborador_alvo.id == $id_ficha_autenticada)
    }

    precondition ($e_para_si || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || ($perfil_autenticado == "GESTOR" && ($e_liderado_direto || $e_do_meu_departamento))) {
      error_type = "accessdenied"
      error = "Voce so pode criar metas para os seus liderados diretos ou para o seu departamento."
    }

    db.get ciclo_avaliacao {
      field_name = "id"
      field_value = $input.ciclo_avaliacao_id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de avaliacao nao encontrado."
    }

    precondition ($ciclo.status == "em_andamento") {
      error_type = "inputerror"
      error = "O ciclo de avaliacao precisa estar em andamento."
    }

    db.add meta_avaliacao {
      data = {
        ciclo_avaliacao_id  : $ciclo.id
        colaborador_id        : $colaborador_alvo.id
        titulo                   : $input.titulo
        descricao                   : $input.descricao
        indicador                      : $input.indicador
        valor_esperado                    : $input.valor_esperado
        unidade_medida                       : $input.unidade_medida
        peso                                    : $input.peso
        data_prazo                                 : $input.data_prazo
        progresso_percentual                          : 0
        status                                           : "planejada"
        criado_por_user_id                                  : $usuario_autenticado.id
        updated_at                                             : "now"
      }
    } as $meta_criada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_meta"
        recurso    : "meta_avaliacao"
        registro_id: $meta_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    conditional {
      if ($e_para_si == false) {
        function.run "ConectaHR/notificar" {
          input = {colaborador_id: $colaborador_alvo.id, autor_user_id: $usuario_autenticado.id, tipo: "acompanhamento_equipe", titulo: "Nova meta para voce", mensagem: $usuario_autenticado.nome ~ " criou a meta \"" ~ $input.titulo ~ "\" para voce.", recurso: "meta_avaliacao", registro_id: $meta_criada.id}
        } as $aviso_meta

        conditional {
          if ($colaborador_alvo.user_id != null) {
            db.get user {
              field_name = "id"
              field_value = $colaborador_alvo.user_id
            } as $usuario_alvo

            conditional {
              if (($usuario_alvo != null) && $usuario_alvo.ativo) {
                db.add email_outbox {
                  data = {
                    destinatario_email: $usuario_alvo.email
                    destinatario_nome : $usuario_alvo.nome
                    assunto           : "ConectaRH - Nova meta para voce"
                    corpo             : "Ola " ~ $usuario_alvo.nome ~ ",\n\n" ~ $usuario_autenticado.nome ~ " criou a meta \"" ~ $input.titulo ~ "\" para voce. Veja os detalhes no ConectaRH, em Trajetoria.\n\nEste e um aviso automatico."
                    chave_idempotencia: "meta_criada_" ~ ($meta_criada.id|to_text)
                  }
                } as $email_meta
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Meta criada com sucesso."
    meta    : $meta_criada
  }

  guid = "conectahr-metas-post-0001"
}
