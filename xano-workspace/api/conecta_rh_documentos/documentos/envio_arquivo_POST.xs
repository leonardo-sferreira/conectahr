// Gera o endereco de envio de um arquivo de documento no Supabase Storage (change anexo-de-arquivos, D2 e D3).
// O plano do Xano nao recebe arquivo: a tela pede este endereco de uso unico e manda o arquivo direto para o
// bucket privado `documentos`; depois cadastra o documento em `documentos` POST com o `arquivo_url` devolvido.
// A chave do Supabase fica so no ambiente do Xano (SUPABASE_URL e SUPABASE_SERVICE_KEY). O caminho e um UUID,
// sem dado pessoal (D5). Pode pedir quem pode cadastrar o documento: RH, ADMIN ou o proprio colaborador.
query "documentos/envio_arquivo" verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int colaborador_id
    text extensao filters=trim|max:10
  }

  stack {
    // Localiza o usuario autenticado.
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

    // Bloqueia contas inativas.
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

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_destino

    precondition ($colaborador_destino != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Mesma regra de `documentos` POST: RH, ADMIN ou o proprio colaborador, checado antes do estado do colaborador.
    var $acesso_administrativo {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")
    }

    var $acesso_proprietario {
      value = ($colaborador_destino.user_id == $usuario_autenticado.id)
    }

    precondition ($acesso_administrativo || $acesso_proprietario) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para enviar documentos para este colaborador."
    }

    var $status_colaborador {
      value = $colaborador_destino.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel enviar documento para colaborador desligado."
    }

    var $extensao {
      value = $input.extensao|to_lower
    }

    // So PDF e foto (o bucket tambem recusa outros tipos, D6).
    precondition ($extensao == "pdf" || $extensao == "jpg" || $extensao == "jpeg" || $extensao == "png") {
      error_type = "inputerror"
      error = "Envie um arquivo PDF, JPG ou PNG."
    }

    precondition ($env.SUPABASE_URL != null && $env.SUPABASE_SERVICE_KEY != null) {
      error_type = "standard"
      error = "O envio de arquivos ainda nao foi configurado. Fale com o RH."
    }

    var $base_supabase {
      value = $env.SUPABASE_URL|trim
    }

    security.create_uuid as $uuid_arquivo

    var $caminho_arquivo {
      value = $uuid_arquivo ~ "." ~ $extensao
    }

    api.request {
      url = $base_supabase ~ "/storage/v1/object/upload/sign/documentos/" ~ $caminho_arquivo
      method = "POST"
      headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
      params = {}
    } as $resposta_supabase

    precondition ($resposta_supabase.response.status == 200 && $resposta_supabase.response.result.url != null) {
      error_type = "standard"
      error = "Nao foi possivel preparar o envio do arquivo agora. Tente de novo em instantes."
    }

    // Auditoria: so o caminho aleatorio e a extensao, sem dado pessoal.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "gerar_envio_arquivo_documento"
        recurso    : "colaborador"
        registro_id: $colaborador_destino.id
        valor_novo : "arquivo=" ~ $caminho_arquivo
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    upload_url : $base_supabase ~ "/storage/v1" ~ $resposta_supabase.response.result.url
    arquivo_url: $base_supabase ~ "/storage/v1/object/documentos/" ~ $caminho_arquivo
  }
  guid = "cxNaG2nmNIShTtXbsBFzVX--Elk"
}
