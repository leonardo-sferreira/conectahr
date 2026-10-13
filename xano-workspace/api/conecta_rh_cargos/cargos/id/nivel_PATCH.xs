// RH e Admin definem o nivel hierarquico de um cargo (change organograma-hierarquia, D3). So o
// nivel: o cargos/{id} PATCH exige nome, descricao e salario juntos. nivel_hierarquico_id vazio tira
// o nivel. Auditado.
query "cargos/{id}/nivel" verb=PATCH {
  api_group = "ConectaRH — Cargos"
  auth = "user"

  input {
    int id
    int? nivel_hierarquico_id?
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem mudar a hierarquia."
    }

    db.get cargo {
      field_name = "id"
      field_value = $input.id
    } as $cargo_atual

    precondition ($cargo_atual != null) {
      error_type = "notfound"
      error = "Cargo nao encontrado."
    }

    conditional {
      if ($input.nivel_hierarquico_id != null) {
        db.get nivel_hierarquico {
          field_name = "id"
          field_value = $input.nivel_hierarquico_id
        } as $nivel_escolhido

        precondition ($nivel_escolhido != null && $nivel_escolhido.ativo) {
          error_type = "inputerror"
          error = "Escolha um nivel ativo."
        }
      }
    }

    db.edit cargo {
      field_name = "id"
      field_value = $cargo_atual.id
      data = {nivel_hierarquico_id: $input.nivel_hierarquico_id, updated_at: "now"}
    } as $cargo_atualizado

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "definir_nivel_cargo"
        recurso       : "cargo"
        registro_id   : $cargo_atual.id
        valor_anterior: ($cargo_atual.nivel_hierarquico_id|to_text)
        valor_novo    : ($input.nivel_hierarquico_id|to_text)
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Nivel do cargo atualizado."
    cargo   : {id: $cargo_atualizado.id, nome: $cargo_atualizado.nome, nivel_hierarquico_id: $cargo_atualizado.nivel_hierarquico_id}
  }

  guid = "conectahr-cargos-id-nivel-patch-0001"
}
