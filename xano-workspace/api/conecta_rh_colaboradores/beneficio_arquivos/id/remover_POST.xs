// Remove um material de beneficio (change apresentacao-de-beneficios, D5): desativa o registro, sem apagar; o arquivo
// fica no bucket (limpeza manual, como os documentos). Somente RH ou Admin; auditado.
query "beneficio_arquivos/{id}/remover" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
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
    db.get beneficio_arquivo {
      field_name = "id"
      field_value = $input.id
    } as $material

    precondition ($material != null && $material.ativo) {
      error_type = "notfound"
      error = "Material nao encontrado."
    }

    db.edit beneficio_arquivo {
      field_name = "id"
      field_value = $material.id
      data = {ativo: false, updated_at: "now"}
    } as $material_removido

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "remover_material_beneficio"
        recurso    : "beneficio_arquivo"
        registro_id: $material.id
        valor_anterior: $material.nome
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso: true
  }
  guid = "o0PX22STdp9iAsJbH-78tyNj5fA"
}