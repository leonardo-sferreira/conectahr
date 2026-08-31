// RH/ADMIN publica um artigo de FAQ. Conteudo sobre beneficios fica
// fora do escopo desta mudanca (ver proposal.md - Non-Goals).
query artigos_faq verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text categoria filters=trim
    text titulo filters=trim|max:200
    text conteudo filters=trim|max:5000
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem publicar artigos de FAQ."
    }

    // Valida a categoria usando os valores exatos do Enum.
    precondition ($input.categoria == "ferias" || $input.categoria == "ponto" || $input.categoria == "documentos" || $input.categoria == "politicas_internas") {
      error_type = "inputerror"
      error = "Categoria invalida. Use ferias, ponto, documentos ou politicas_internas."
    }

    db.add artigo_faq {
      data = {
        categoria           : $input.categoria
        titulo                 : $input.titulo
        conteudo                  : $input.conteudo
        publicado_por_user_id        : $usuario_autenticado.id
        ativo                            : true
        updated_at                          : "now"
      }
    } as $artigo_criado
  }

  response = {
    sucesso : true
    mensagem: "Artigo publicado com sucesso."
    artigo  : $artigo_criado
  }

  guid = "conectahr-artigos-faq-post-0001"
}
