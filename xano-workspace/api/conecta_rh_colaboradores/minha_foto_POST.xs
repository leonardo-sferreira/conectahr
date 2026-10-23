// Grava a foto de perfil da propria pessoa (change foto-de-perfil, D3): o caminho devolvido por minha_foto/envio,
// depois do envio. Confere o formato do caminho ({uuid}.webp) e que o arquivo existe no bucket (o Supabase so assina
// arquivo que existe). Apaga a foto anterior do bucket e audita alterar_foto_perfil, sem o caminho. Age so sobre a
// ficha de quem esta logado: nao ha como gravar a foto de outra pessoa.
query "minha_foto" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text caminho filters=trim|lower
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

    precondition ((($input.caminho|strlen) == 41) && ($input.caminho|ends_with:".webp") && (($input.caminho|contains:"/") == false) && (($input.caminho|contains:"..") == false)) {
      error_type = "inputerror"
      error = "Caminho de foto invalido."
    }

    precondition ($env.SUPABASE_URL != null && $env.SUPABASE_SERVICE_KEY != null) {
      error_type = "standard"
      error = "O envio de arquivos ainda nao foi configurado. Fale com o RH."
    }

    var $lista_caminho {
      value = [$input.caminho]
    }

    function.run "ConectaHR/assinar_fotos" {
      input = {caminhos: $lista_caminho}
    } as $assinadas

    var $url_nova {
      value = $assinadas|get:$input.caminho
    }

    precondition ($url_nova != null) {
      error_type = "inputerror"
      error = "A foto ainda nao chegou ao armazenamento. Envie de novo."
    }

    var $caminho_anterior {
      value = $colaborador_autenticado.foto_path
    }

    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador_autenticado.id
      data = {
        foto_path : $input.caminho
        updated_at: "now"
      }
    } as $colaborador_editado

    conditional {
      if (($caminho_anterior != null) && ($caminho_anterior != $input.caminho)) {
        function.run "ConectaHR/apagar_foto" {
          input = {caminho: $caminho_anterior}
        } as $apagou_anterior
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "alterar_foto_perfil"
        recurso    : "colaborador"
        registro_id: $colaborador_autenticado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Foto atualizada."
    foto_url: $url_nova
  }

  guid = "conectahr-minha-foto-post-0001"
}
