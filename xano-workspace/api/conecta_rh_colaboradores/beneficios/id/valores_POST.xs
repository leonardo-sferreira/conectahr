// Altera o valor da empresa e o desconto de um beneficio para todos (tarefa 85): grava o padrao do
// catalogo e aplica a cada vinculo vigente. Quem tem valor personalizado so muda com
// incluir_personalizados. Cada pessoa alterada recebe o aviso no sino. Somente RH ou Admin.
query "beneficios/{id}/valores" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    decimal valor_empresa filters=min:0
    decimal desconto_colaborador filters=min:0
    bool incluir_personalizados?=false
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

    precondition ($beneficio.ativo) {
      error_type = "inputerror"
      error = "Beneficio removido do catalogo. Reative antes de alterar os valores."
    }

    db.edit beneficio {
      field_name = "id"
      field_value = $beneficio.id
      data = {valor_empresa_padrao: $input.valor_empresa, desconto_padrao: $input.desconto_colaborador, updated_at: "now"}
    } as $beneficio_atualizado

    db.query colaborador_beneficio {
      where = $db.colaborador_beneficio.beneficio_id == $beneficio.id && $db.colaborador_beneficio.ativo == true
      return = {type: "list"}
    } as $vinculos_do_beneficio

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $alterados {
      value = 0
    }

    var $mantidos_personalizados {
      value = 0
    }

    foreach ($vinculos_do_beneficio) {
      each as $vinculo_valor {
        conditional {
          if ($vinculo_valor.data_fim == null || $vinculo_valor.data_fim >= $hoje) {
            conditional {
              if ($vinculo_valor.valor_personalizado && $input.incluir_personalizados == false) {
                var.update $mantidos_personalizados {
                  value = $mantidos_personalizados + 1
                }
              }

              else {
                db.edit colaborador_beneficio {
                  field_name = "id"
                  field_value = $vinculo_valor.id
                  data = {valor_empresa: $input.valor_empresa, desconto_colaborador: $input.desconto_colaborador, valor_personalizado: false, updated_at: "now"}
                } as $vinculo_alterado

                db.get colaborador {
                  field_name = "id"
                  field_value = $vinculo_valor.colaborador_id
                } as $pessoa_aviso

                conditional {
                  if ($pessoa_aviso != null && $pessoa_aviso.user_id != null) {
                    db.add notificacao_interna {
                      data = {
                        destinatario_user_id: $pessoa_aviso.user_id
                        tipo                : "beneficio_atualizado"
                        titulo              : "Os valores do beneficio " ~ $beneficio.nome ~ " mudaram"
                        mensagem            : "A partir de agora a empresa paga R$ " ~ ($input.valor_empresa|to_text) ~ " e o desconto e de R$ " ~ ($input.desconto_colaborador|to_text) ~ " por mes. Veja em Beneficios."
                        recurso             : "beneficio"
                        registro_id         : $vinculo_valor.beneficio_id
                      }
                    } as $aviso_beneficio
                  }
                }

                var.update $alterados {
                  value = $alterados + 1
                }
              }
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id     : $usuario_autenticado.id
        acao        : "alterar_valores_beneficio_todos"
        recurso     : "beneficio"
        registro_id : $beneficio.id
        valor_antigo: "empresa=" ~ ($beneficio.valor_empresa_padrao|to_text) ~ "; desconto=" ~ ($beneficio.desconto_padrao|to_text)
        valor_novo  : "empresa=" ~ ($input.valor_empresa|to_text) ~ "; desconto=" ~ ($input.desconto_colaborador|to_text) ~ "; alterados=" ~ ($alterados|to_text) ~ "; mantidos=" ~ ($mantidos_personalizados|to_text)
        resultado   : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso                : true
    beneficio              : $beneficio_atualizado
    alterados              : $alterados
    mantidos_personalizados: $mantidos_personalizados
  }

  guid = "conectahr-beneficios-valores-post-0001"
}
