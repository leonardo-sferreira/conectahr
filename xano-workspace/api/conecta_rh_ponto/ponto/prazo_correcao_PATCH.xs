// Define o prazo para pedir correcao de ponto (tarefa 83). Somente RH ou Admin. Nulo tira o
// limite. O ajuste direto do gestor e do RH (folha_ponto/ajustar) nao tem prazo.
query "ponto/prazo_correcao" verb=PATCH {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int? prazo_dias? filters=min:1|max:3650
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
      error = "Somente RH ou Admin podem definir o prazo de correcao do ponto."
    }

    db.query configuracao {
      where = $db.configuracao.chave == "prazo_correcao_ponto_dias"
      return = {type: "single"}
    } as $config_atual

    conditional {
      if ($config_atual == null) {
        db.add configuracao {
          data = {chave: "prazo_correcao_ponto_dias", valor_inteiro: $input.prazo_dias, atualizado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
        } as $config_criada
      }
    }

    conditional {
      if ($config_atual != null) {
        db.edit configuracao {
          field_name = "id"
          field_value = $config_atual.id
          data = {valor_inteiro: $input.prazo_dias, atualizado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
        } as $config_editada
      }
    }

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "definir_prazo_correcao_ponto"
        recurso       : "configuracao"
        valor_anterior: ($config_atual != null ? ($config_atual.valor_inteiro|to_text) : "")
        valor_novo    : ($input.prazo_dias|to_text)
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    prazo_dias : $input.prazo_dias
  }

  guid = "conectahr-ponto-prazo-correcao-patch-0001"
}
