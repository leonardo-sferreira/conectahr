// RH ou Admin remove a foto de perfil de um colaborador, por ser inadequada (change foto-de-perfil, D4): com
// justificativa de 10 a 500 caracteres, auditada (remover_foto_perfil, com a justificativa) e com aviso a pessoa no
// sino. O RH nao envia foto por ninguem.
query "colaboradores/{id}/foto" verb=DELETE {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text justificativa filters=trim
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

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem remover a foto de outra pessoa."
    }

    precondition ((($input.justificativa|strlen) >= 10) && (($input.justificativa|strlen) <= 500)) {
      error_type = "inputerror"
      error = "Escreva a justificativa (de 10 a 500 caracteres)."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    precondition ($colaborador_alvo.foto_path != null) {
      error_type = "inputerror"
      error = "Esta pessoa nao tem foto de perfil."
    }

    var $caminho_anterior {
      value = $colaborador_alvo.foto_path
    }

    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador_alvo.id
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
        user_id      : $usuario_autenticado.id
        acao         : "remover_foto_perfil"
        recurso      : "colaborador"
        registro_id  : $colaborador_alvo.id
        resultado    : "sucesso"
        justificativa: $input.justificativa
      }
    } as $evento_auditoria

    var $mensagem_aviso {
      value = ("O RH removeu sua foto de perfil: " ~ $input.justificativa)|substr:0:1000
    }

    function.run "ConectaHR/notificar" {
      input = {colaborador_id: $colaborador_alvo.id, autor_user_id: $usuario_autenticado.id, tipo: "cadastro_atualizado", titulo: "Sua foto de perfil foi removida", mensagem: $mensagem_aviso, recurso: "colaborador", registro_id: $colaborador_alvo.id}
    } as $aviso_pessoa
  }

  response = {
    sucesso : true
    mensagem: "Foto removida."
  }

  guid = "conectahr-colaboradores-id-foto-delete-0001"
}
