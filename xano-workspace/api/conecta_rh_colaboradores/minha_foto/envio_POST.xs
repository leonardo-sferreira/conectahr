// Prepara o envio da foto de perfil da propria pessoa (change foto-de-perfil, D1 a D3): garante o bucket privado
// fotos-perfil (cria na primeira vez; se ja existe, o Supabase recusa e segue) e devolve um endereco de envio de uso unico
// para um caminho novo {uuid}.webp. A tela trata a imagem antes (256 x 256 WebP, sem metadados) e depois grava o
// caminho em minha_foto POST. A chave do Supabase fica so no Xano. Qualquer perfil com ficha, nao desligado.
query "minha_foto/envio" verb=POST {
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

    precondition ($colaborador_autenticado.status != "Desligado") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao envia foto."
    }

    precondition ($env.SUPABASE_URL != null && $env.SUPABASE_SERVICE_KEY != null) {
      error_type = "standard"
      error = "O envio de arquivos ainda nao foi configurado. Fale com o RH."
    }

    var $base_supabase {
      value = $env.SUPABASE_URL|trim
    }

    // O bucket e criado so na primeira vez; depois o Supabase responde que ja existe, e isso nao e erro.
    api.request {
      url = $base_supabase ~ "/storage/v1/bucket"
      method = "POST"
      headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
      params = {id: "fotos-perfil", name: "fotos-perfil", public: false, file_size_limit: 1048576, allowed_mime_types: ["image/webp"]}
    } as $resposta_bucket

    security.create_uuid as $uuid_foto

    var $caminho_foto {
      value = $uuid_foto ~ ".webp"
    }

    api.request {
      url = $base_supabase ~ "/storage/v1/object/upload/sign/fotos-perfil/" ~ $caminho_foto
      method = "POST"
      headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
      params = {}
    } as $resposta_envio

    precondition ($resposta_envio.response.status == 200 && $resposta_envio.response.result.url != null) {
      error_type = "standard"
      error = "Nao foi possivel preparar o envio da foto agora. Tente de novo em instantes."
    }
  }

  response = {
    sucesso   : true
    upload_url: ($env.SUPABASE_URL|trim) ~ "/storage/v1" ~ $resposta_envio.response.result.url
    caminho   : $caminho_foto
  }

  guid = "conectahr-minha-foto-envio-post-0001"
}
