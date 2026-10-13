// Gera o endereco de envio de um material de beneficio no Supabase (change apresentacao-de-beneficios, D1): mesmo
// bucket privado e mesmo fluxo de documentos/envio_arquivo, na pasta beneficios/. Depois de enviar o arquivo, a tela
// registra o material em beneficios/{id}/arquivos POST. Somente RH ou Admin.
query "beneficios/{id}/arquivos/envio" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text extensao filters=trim|max:10
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

    var $extensao {
      value = $input.extensao|to_lower
    }

    precondition ($extensao == "pdf" || $extensao == "jpg" || $extensao == "jpeg" || $extensao == "png") {
      error_type = "inputerror"
      error = "Envie um arquivo PDF, JPG ou PNG."
    }

    // Mesmos cabecalhos de documentos/envio_arquivo: a chave service_role vai no apikey e no Authorization.
    precondition ($env.SUPABASE_URL != null && $env.SUPABASE_SERVICE_KEY != null) {
      error_type = "standard"
      error = "O envio de arquivos ainda nao foi configurado. Fale com o RH."
    }

    var $base_supabase {
      value = $env.SUPABASE_URL|trim
    }
    security.create_uuid as $uuid_material

    var $caminho_material {
      value = "beneficios/" ~ $uuid_material ~ "." ~ $extensao
    }

    api.request {
      url = $base_supabase ~ "/storage/v1/object/upload/sign/documentos/" ~ $caminho_material
      method = "POST"
      headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
      params = {}
    } as $resposta_supabase

    precondition ($resposta_supabase.response.status == 200 && $resposta_supabase.response.result.url != null) {
      error_type = "standard"
      error = "Nao foi possivel preparar o envio do arquivo agora. Tente de novo em instantes."
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "gerar_envio_material_beneficio"
        recurso    : "beneficio"
        registro_id: $beneficio.id
        valor_novo : "arquivo=" ~ $caminho_material
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    upload_url: $base_supabase ~ "/storage/v1" ~ $resposta_supabase.response.result.url
    caminho   : $caminho_material
  }
  guid = "g4t1I6QdJ2W9C0d62tazkbp2ydE"
}