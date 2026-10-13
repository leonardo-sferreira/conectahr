// Registra um material ja enviado ao Supabase (change apresentacao-de-beneficios, D1 e D5): nome que o colaborador ve
// e o caminho gerado por beneficios/{id}/arquivos/envio. Somente RH ou Admin; auditado, sem aviso no sino.
query "beneficios/{id}/arquivos" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:100
    text caminho filters=trim|max:200
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

    // So caminhos gerados pelo envio: pasta beneficios/, sem subir de pasta.
    precondition (($input.caminho|starts_with:"beneficios/") && ($input.caminho|contains:"..") == false && ($input.caminho|split:"/"|count) == 2) {
      error_type = "inputerror"
      error = "Arquivo invalido. Envie o material de novo."
    }

    db.add beneficio_arquivo {
      data = {beneficio_id: $beneficio.id, nome: $input.nome, caminho: $input.caminho, ativo: true, criado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
    } as $material

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "anexar_material_beneficio"
        recurso    : "beneficio_arquivo"
        registro_id: $material.id
        valor_novo : "beneficio=" ~ ($beneficio.id|to_text) ~ "; nome=" ~ $input.nome
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    material: {id: $material.id, nome: $material.nome}
  }
  guid = "eXqcjm-gM_lfPTZuibJ3f2PA9N4"
}