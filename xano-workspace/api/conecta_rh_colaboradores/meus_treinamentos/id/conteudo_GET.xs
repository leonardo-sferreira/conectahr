// Endereco do conteudo de um treinamento de PDF ou apresentacao (change cards-de-treinamentos, D2 e D5): o link do
// Google Drive ou do Slides como esta, ou uma URL assinada de 10 minutos do bucket privado treinamentos. So para quem
// esta no publico do treinamento ativo; os demais recebem 404. Qualquer perfil com ficha.
query "meus_treinamentos/{id}/conteudo" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.get treinamento {
      field_name = "id"
      field_value = $input.id
    } as $treinamento

    var $meu_departamento {
      value = "," ~ ($colaborador_autenticado.departamento_id|to_text) ~ ","
    }

    var $ids_publico {
      value = ($treinamento == null || $treinamento.departamento_ids == null) ? "" : $treinamento.departamento_ids
    }

    // So quem esta no publico do treinamento ativo; os demais recebem 404, como se ele nao existisse.
    precondition (($treinamento != null) && ($treinamento.ativo == true) && (($treinamento.publico == "todos") || ($ids_publico|contains:$meu_departamento))) {
      error_type = "notfound"
      error = "Treinamento nao encontrado."
    }

    var $tipo_conteudo {
      value = ($treinamento.conteudo_tipo == null) ? "video" : $treinamento.conteudo_tipo
    }

    precondition ($tipo_conteudo != "video") {
      error_type = "inputerror"
      error = "Este treinamento e em video: ele toca na propria tela."
    }

    var $url_conteudo {
      value = $treinamento.conteudo_url
    }

    conditional {
      if ($treinamento.conteudo_path != null) {
        precondition ($env.SUPABASE_URL != null && $env.SUPABASE_SERVICE_KEY != null) {
          error_type = "standard"
          error = "Os arquivos ainda nao foram configurados. Fale com o RH."
        }

        api.request {
          url = ($env.SUPABASE_URL|trim) ~ "/storage/v1/object/sign/treinamentos/" ~ $treinamento.conteudo_path
          method = "POST"
          headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
          params = {expiresIn: 600}
        } as $resposta_assinatura

        precondition ($resposta_assinatura.response.status == 200 && $resposta_assinatura.response.result.signedURL != null) {
          error_type = "standard"
          error = "Nao foi possivel abrir o arquivo agora. Tente de novo em instantes."
        }

        var.update $url_conteudo {
          value = ($env.SUPABASE_URL|trim) ~ "/storage/v1" ~ $resposta_assinatura.response.result.signedURL
        }
      }
    }

    precondition ($url_conteudo != null) {
      error_type = "notfound"
      error = "Este treinamento ainda nao tem conteudo."
    }
  }

  response = {
    sucesso: true
    tipo   : $tipo_conteudo
    arquivo: ($treinamento.conteudo_path != null)
    url    : $url_conteudo
  }

  guid = "conectahr-meus-treinamentos-conteudo-get-0001"
}
