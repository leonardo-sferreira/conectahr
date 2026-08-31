// Define o gestor responsável por um departamento.
// Somente RH ou ADMIN podem realizar esta operação.
query "departamentos/{id}/gestor" verb=PATCH {
  api_group = "ConectaRH — Departamentos"
  auth = "user"

  input {
    int id
    int gestor_colaborador_id
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Valida o perfil de quem executa a operação.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem definir o gestor de um departamento."
    }
  
    // Localiza o departamento.
    db.get departamento {
      field_name = "id"
      field_value = $input.id
    } as $departamento_alvo
  
    precondition ($departamento_alvo != null) {
      error_type = "notfound"
      error = "Departamento não encontrado."
    }
  
    precondition ($departamento_alvo.ativo) {
      error_type = "inputerror"
      error = "Não é possível definir gestor para um departamento inativo."
    }
  
    // Localiza o colaborador pelo ID recebido.
    db.get colaborador {
      field_name = "id"
      field_value = $input.gestor_colaborador_id
    } as $colaborador_selecionado
  
    precondition ($colaborador_selecionado != null) {
      error_type = "notfound"
      error = "Colaborador selecionado como gestor não encontrado."
    }
  
    // Valida o status profissional.
    var $status_colaborador {
      value = $colaborador_selecionado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "inputerror"
      error = "O colaborador selecionado não está com status ativo."
    }
  
    // Confere o departamento do colaborador.
    precondition ($colaborador_selecionado.departamento_id == $departamento_alvo.id) {
      error_type = "inputerror"
      error = "O colaborador selecionado não pertence a este departamento."
    }
  
    // Confere se existe uma conta vinculada.
    precondition ($colaborador_selecionado.user_id != null) {
      error_type = "inputerror"
      error = "O colaborador selecionado não possui uma conta de acesso vinculada."
    }
  
    // Localiza a conta vinculada ao colaborador.
    db.get user {
      field_name = "id"
      field_value = $colaborador_selecionado.user_id
    } as $conta_do_gestor
  
    precondition ($conta_do_gestor != null) {
      error_type = "notfound"
      error = "A conta de acesso vinculada ao colaborador não foi encontrada."
    }
  
    precondition ($conta_do_gestor.ativo) {
      error_type = "inputerror"
      error = "A conta de acesso do gestor está inativa."
    }
  
    // Confere o perfil da conta.
    var $perfil_da_conta {
      value = $conta_do_gestor.perfil|trim|to_upper
    }
  
    precondition ($perfil_da_conta == "GESTOR") {
      error_type = "inputerror"
      error = "A conta vinculada ao colaborador precisa possuir o perfil Gestor."
    }

    // Evita substituicao redundante pelo mesmo gestor ja vigente.
    precondition ($departamento_alvo.gestor_colaborador_id != $colaborador_selecionado.id) {
      error_type = "inputerror"
      error = "Este colaborador ja e o gestor vigente deste departamento."
    }

    // Localiza o vinculo de gestor ainda aberto, se existir, para encerra-lo.
    db.query historico_gestor_departamento {
      where = $db.historico_gestor_departamento.departamento_id == $departamento_alvo.id && $db.historico_gestor_departamento.data_fim == null
      return = {type: "single"}
    } as $vinculo_atual

    // Registra o gestor no departamento e preserva o historico na mesma transacao.
    db.transaction {
      stack {
        db.edit departamento {
          field_name = "id"
          field_value = $departamento_alvo.id
          data = {
            gestor_colaborador_id: $colaborador_selecionado.id
            updated_at           : "now"
          }
        } as $departamento_atualizado

        conditional {
          if ($vinculo_atual != null) {
            db.edit historico_gestor_departamento {
              field_name = "id"
              field_value = $vinculo_atual.id
              data = {data_fim: "now", updated_at: "now"}
            } as $vinculo_encerrado
          }
        }

        db.add historico_gestor_departamento {
          data = {
            departamento_id      : $departamento_alvo.id
            colaborador_id        : $colaborador_selecionado.id
            data_inicio           : "now"
            data_fim               : null
            definido_por_user_id  : $usuario_autenticado.id
            updated_at             : "now"
          }
        } as $vinculo_criado

        // Auditoria: troca de gestor do departamento.
        db.add auditoria {
          data = {
            user_id       : $usuario_autenticado.id
            acao          : "definir_gestor_departamento"
            recurso       : "departamento"
            registro_id   : $departamento_alvo.id
            valor_anterior: ($departamento_alvo.gestor_colaborador_id|to_text)
            valor_novo    : ($colaborador_selecionado.id|to_text)
            resultado     : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso              : true
    mensagem             : "Gestor definido com sucesso."
    departamento         : $departamento_atualizado
    gestor_colaborador_id: $colaborador_selecionado.id
    gestor_nome          : $colaborador_selecionado.nome
  }

  guid = "ptQz5Oioyl4S1WFXdc1mYych8mk"
}