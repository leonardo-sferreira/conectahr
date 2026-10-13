// RH e Admin editam o nome, a ordem ou a situacao de um nivel hierarquico (change
// organograma-hierarquia, D3). Desativar nao apaga: o cargo continua ligado, so deixa de ser rotulado.
query "niveis_hierarquicos/{id}" verb=PATCH {
  api_group = "ConectaRH — Cargos"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:60
    int ordem filters=min:1|max:99
    bool ativo
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem mudar a hierarquia."
    }

    db.get nivel_hierarquico {
      field_name = "id"
      field_value = $input.id
    } as $nivel_atual

    precondition ($nivel_atual != null) {
      error_type = "notfound"
      error = "Nivel nao encontrado."
    }

    db.query nivel_hierarquico {
      where = $db.nivel_hierarquico.nome == $input.nome && $db.nivel_hierarquico.id != $input.id
      return = {type: "single"}
    } as $mesmo_nome

    precondition ($mesmo_nome == null) {
      error_type = "inputerror"
      error = "Ja existe um nivel com esse nome."
    }

    db.edit nivel_hierarquico {
      field_name = "id"
      field_value = $nivel_atual.id
      data = {nome: $input.nome, ordem: $input.ordem, ativo: $input.ativo, updated_at: "now"}
    } as $nivel_atualizado

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "editar_nivel_hierarquico"
        recurso       : "nivel_hierarquico"
        registro_id   : $nivel_atual.id
        valor_anterior: "nome=" ~ $nivel_atual.nome ~ "; ordem=" ~ ($nivel_atual.ordem|to_text) ~ "; ativo=" ~ ($nivel_atual.ativo|to_text)
        valor_novo    : "nome=" ~ $input.nome ~ "; ordem=" ~ ($input.ordem|to_text) ~ "; ativo=" ~ ($input.ativo|to_text)
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Nivel atualizado."
    nivel   : $nivel_atualizado
  }

  guid = "conectahr-niveis-hierarquicos-id-patch-0001"
}
