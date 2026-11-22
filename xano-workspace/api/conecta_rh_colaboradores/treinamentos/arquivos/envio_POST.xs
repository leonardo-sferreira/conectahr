// Prepara o envio de um material de treinamento (change cards-de-treinamentos, D2): o PDF (ate 20 MB) ou a capa (WebP
// 640 x 360, ja reduzida pelo servidor do Streamlit). Garante o bucket privado "treinamentos" (criado na primeira vez) e
// devolve o endereco de envio de uso unico com o caminho "{uuid}.pdf" ou "{uuid}.webp". Material da empresa, sem dado
// pessoal. So RH e Admin. Auditado.
query "treinamentos/arquivos/envio" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text tipo filters=trim|lower
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    precondition (($input.tipo == "pdf") || ($input.tipo == "capa")) {
      error_type = "inputerror"
      error = "Tipo de arquivo invalido. Use pdf ou capa."
    }

    precondition ($env.SUPABASE_URL != null && $env.SUPABASE_SERVICE_KEY != null) {
      error_type = "standard"
      error = "O envio de arquivos ainda nao foi configurado. Fale com o Admin."
    }

    var $base_supabase {
      value = $env.SUPABASE_URL|trim
    }

    // O bucket e criado so na primeira vez; depois o Supabase responde que ja existe, e isso nao e erro.
    api.request {
      url = $base_supabase ~ "/storage/v1/bucket"
      method = "POST"
      headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
      params = {id: "treinamentos", name: "treinamentos", public: false, file_size_limit: 20971520, allowed_mime_types: ["application/pdf", "image/webp"]}
    } as $resposta_bucket

    security.create_uuid as $uuid_arquivo

    var $caminho_arquivo {
      value = $uuid_arquivo ~ (($input.tipo == "pdf") ? ".pdf" : ".webp")
    }

    api.request {
      url = $base_supabase ~ "/storage/v1/object/upload/sign/treinamentos/" ~ $caminho_arquivo
      method = "POST"
      headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
      params = {}
    } as $resposta_envio

    precondition ($resposta_envio.response.status == 200 && $resposta_envio.response.result.url != null) {
      error_type = "standard"
      error = "Nao foi possivel preparar o envio agora. Tente de novo em instantes."
    }

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "gerar_envio_material_treinamento"
        recurso      : "treinamento"
        justificativa: $input.tipo
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    upload_url: ($env.SUPABASE_URL|trim) ~ "/storage/v1" ~ $resposta_envio.response.result.url
    caminho   : $caminho_arquivo
  }

  guid = "conectahr-treinamentos-arquivos-envio-post-0001"
}
