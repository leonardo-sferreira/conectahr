// Ativa ou remove um beneficio do catalogo (tarefas 82 e 85). Somente RH ou Admin. Remover (ativo =
// false) impede novos vinculos e encerra hoje o beneficio de todos que o tem, sem apagar o
// historico; cada pessoa recebe o aviso no sino. Reativar nao devolve os vinculos encerrados.
query "beneficios/{id}/status" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    bool ativo
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    db.get beneficio {
      field_name = "id"
      field_value = $input.id
    } as $beneficio

    precondition ($beneficio != null) {
      error_type = "notfound"
      error = "Beneficio nao encontrado."
    }

    db.edit beneficio {
      field_name = "id"
      field_value = $beneficio.id
      data = {ativo: $input.ativo, updated_at: "now"}
    } as $beneficio_atualizado

    var $encerrados {
      value = 0
    }

    conditional {
      if ($input.ativo == false && $beneficio.ativo) {
        db.query colaborador_beneficio {
          where = $db.colaborador_beneficio.beneficio_id == $beneficio.id && $db.colaborador_beneficio.ativo == true
          return = {type: "list"}
        } as $vinculos_do_beneficio

        var $hoje {
          value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
        }

        foreach ($vinculos_do_beneficio) {
          each as $vinculo_remover {
            conditional {
              if ($vinculo_remover.data_fim == null || $vinculo_remover.data_fim >= $hoje) {
                db.edit colaborador_beneficio {
                  field_name = "id"
                  field_value = $vinculo_remover.id
                  data = {data_fim: ($vinculo_remover.data_inicio > $hoje ? $vinculo_remover.data_inicio : $hoje), ativo: false, encerrado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
                } as $vinculo_encerrado

                db.get colaborador {
                  field_name = "id"
                  field_value = $vinculo_remover.colaborador_id
                } as $pessoa_aviso

                conditional {
                  if ($pessoa_aviso != null && $pessoa_aviso.user_id != null) {
                    db.add notificacao_interna {
                      data = {
                        destinatario_user_id: $pessoa_aviso.user_id
                        tipo                : "beneficio_atualizado"
                        titulo              : "O beneficio " ~ $beneficio.nome ~ " foi encerrado"
                        mensagem            : "A empresa deixou de oferecer o beneficio " ~ $beneficio.nome ~ ". Ele fica no seu historico. Duvidas: fale com o RH."
                        recurso             : "beneficio"
                        registro_id         : $vinculo_remover.beneficio_id
                      }
                    } as $aviso_beneficio
                  }
                }

                var.update $encerrados {
                  value = $encerrados + 1
                }
              }
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "alterar_status_beneficio"
        recurso    : "beneficio"
        registro_id: $beneficio.id
        valor_novo : ($input.ativo|to_text) ~ "; encerrados=" ~ ($encerrados|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    beneficio : $beneficio_atualizado
    encerrados: $encerrados
  }

  guid = "conectahr-beneficios-status-patch-0001"
}
