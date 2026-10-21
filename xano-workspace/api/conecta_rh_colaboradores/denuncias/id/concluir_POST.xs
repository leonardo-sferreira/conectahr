// A comissao de etica conclui a apuracao (change canal-de-denuncias, D4) com o resultado (procedente,
// improcedente ou inconclusiva) e o parecer final, que quem denunciou le pelo codigo. Concluida, nao reabre.
// Auditado com o resultado (sem o texto do parecer). So membro ativo da comissao.
query "denuncias/{id}/concluir" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text resultado filters=trim|lower
    text parecer filters=trim|max:4000
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

    db.query comissao_etica {
      where = $db.comissao_etica.user_id == $usuario_autenticado.id && $db.comissao_etica.ativo == true
      return = {type: "single"}
    } as $membro_comissao

    precondition ($membro_comissao != null) {
      error_type = "accessdenied"
      error = "So a comissao de etica ve as denuncias."
    }

    db.get denuncia {
      field_name = "id"
      field_value = $input.id
    } as $denuncia

    precondition ($denuncia != null) {
      error_type = "notfound"
      error = "Denuncia nao encontrada."
    }

    precondition ($denuncia.status != "concluida") {
      error_type = "inputerror"
      error = "Esta denuncia ja foi concluida."
    }

    precondition (($input.resultado == "procedente") || ($input.resultado == "improcedente") || ($input.resultado == "inconclusiva")) {
      error_type = "inputerror"
      error = "Resultado invalido. Use procedente, improcedente ou inconclusiva."
    }

    precondition (($input.parecer|strlen) >= 10) {
      error_type = "inputerror"
      error = "Escreva o parecer final (pelo menos 10 caracteres)."
    }

    db.edit denuncia {
      field_name = "id"
      field_value = $denuncia.id
      data = {status: "concluida", resultado: $input.resultado, parecer: $input.parecer, concluida_em: $hoje}
    } as $denuncia_concluida

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "concluir_denuncia"
        recurso      : "denuncia"
        registro_id  : $denuncia.id
        resultado    : "sucesso"
        justificativa: $input.resultado
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Apuracao concluida."
  }

  guid = "conectahr-denuncias-concluir-post-0001"
}
