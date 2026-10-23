// Remove a foto de perfil da propria pessoa (change foto-de-perfil, D3): apaga o arquivo do bucket, anula
// foto_path e audita remover_foto_perfil. Sem foto, so confirma. Depois disso, aparecem as iniciais.
query "minha_foto" verb=DELETE {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    var $caminho_anterior {
      value = $colaborador_autenticado.foto_path
    }

    conditional {
      if ($caminho_anterior != null) {
        db.edit colaborador {
          field_name = "id"
          field_value = $colaborador_autenticado.id
          data = {
            foto_path : null
            updated_at: "now"
          }
        } as $colaborador_editado

        function.run "ConectaHR/apagar_foto" {
          input = {caminho: $caminho_anterior}
        } as $apagou

        db.add auditoria {
          data = {
            user_id    : $usuario_autenticado.id
            acao       : "remover_foto_perfil"
            recurso    : "colaborador"
            registro_id: $colaborador_autenticado.id
            resultado  : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Foto removida."
  }

  guid = "conectahr-minha-foto-delete-0001"
}
