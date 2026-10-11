// Define ou limpa o superior direto de um colaborador (tarefa 81). Somente RH ou Admin.
// O superior aprova as alteracoes de ponto da pessoa e consulta a folha dela. Nao aceita a
// propria pessoa, colaborador desligado nem um ciclo (A acima de B acima de A).
query "colaboradores/{id}/superior" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int? superior_colaborador_id?
  }

  stack {
    // Localiza o usuario autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh
  
    precondition ($usuario_rh != null) {
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
  
    // Bloqueia contas inativas.
    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_rh.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }
  
    // Somente RH pode atualizar vinculos profissionais.
    precondition ($perfil_rh == "RH" || $perfil_rh == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem definir o superior direto."
    }
  
    // Localiza o colaborador.
    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    conditional {
      if ($input.superior_colaborador_id != null) {
        precondition ($input.superior_colaborador_id != $input.id) {
          error_type = "inputerror"
          error = "A pessoa nao pode ser superior de si mesma."
        }

        db.get colaborador {
          field_name = "id"
          field_value = $input.superior_colaborador_id
        } as $superior

        precondition ($superior != null) {
          error_type = "notfound"
          error = "Superior nao encontrado."
        }

        precondition (($superior.status|trim|to_upper) != "DESLIGADO") {
          error_type = "inputerror"
          error = "O superior nao pode ser um colaborador desligado."
        }

        // Ciclo: sobe a cadeia de superiores a partir do novo superior (ate 20 niveis).
        var $atual_id {
          value = $superior.superior_colaborador_id
        }

        var $niveis {
          value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        }

        foreach ($niveis) {
          each as $nivel {
            conditional {
              if ($atual_id != null) {
                precondition ($atual_id != $input.id) {
                  error_type = "inputerror"
                  error = "Isso criaria um ciclo na hierarquia (a pessoa ficaria acima do proprio superior)."
                }

                db.get colaborador {
                  field_name = "id"
                  field_value = $atual_id
                } as $acima

                var.update $atual_id {
                  value = ($acima != null ? $acima.superior_colaborador_id : null)
                }
              }
            }
          }
        }
      }
    }

    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador_alvo.id
      data = {superior_colaborador_id: $input.superior_colaborador_id, updated_at: "now"}
    } as $colaborador_atualizado

    db.add auditoria {
      data = {
        user_id       : $usuario_rh.id
        acao          : "definir_superior"
        recurso       : "colaborador"
        registro_id   : $colaborador_alvo.id
        valor_anterior: ($colaborador_alvo.superior_colaborador_id|to_text)
        valor_novo    : ($input.superior_colaborador_id|to_text)
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso                 : true
    mensagem                : "Superior direto atualizado."
    superior_colaborador_id : $colaborador_atualizado.superior_colaborador_id
  }

  guid = "conectahr-colaboradores-superior-patch-0001"
}
