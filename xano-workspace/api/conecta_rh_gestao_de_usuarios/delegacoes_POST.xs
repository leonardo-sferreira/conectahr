// Cria uma delegacao temporaria de aprovacao. O titular delega a um
// substituto por um escopo e periodo definidos. Bloqueia autoaprovacao
// (titular nao pode delegar para si mesmo). RH/ADMIN podem criar em
// nome de qualquer titular; o proprio usuario pode criar delegando a
// propria autoridade.
query delegacoes verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int? titular_user_id?
    int substituto_user_id
    text escopo filters=trim
    date data_inicio
    date data_fim
    text motivo filters=trim|min:5|max:1000
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

    // Define o titular: o proprio autenticado, ou outro quando RH/ADMIN informar.
    var $titular_id_final {
      value = $usuario_autenticado.id
    }

    conditional {
      if ($input.titular_user_id != null && $input.titular_user_id != $usuario_autenticado.id) {
        precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
          error_type = "accessdenied"
          error = "Somente RH ou ADMIN podem criar delegacao em nome de outro titular."
        }

        var.update $titular_id_final {
          value = $input.titular_user_id
        }
      }
    }

    // Bloqueia autoaprovacao: titular nao pode delegar para si mesmo.
    precondition ($titular_id_final != $input.substituto_user_id) {
      error_type = "inputerror"
      error = "O titular nao pode delegar para si mesmo."
    }

    db.get user {
      field_name = "id"
      field_value = $titular_id_final
    } as $titular

    precondition ($titular != null) {
      error_type = "notfound"
      error = "Titular nao encontrado."
    }

    db.get user {
      field_name = "id"
      field_value = $input.substituto_user_id
    } as $substituto

    precondition ($substituto != null) {
      error_type = "notfound"
      error = "Substituto nao encontrado."
    }

    precondition ($substituto.ativo) {
      error_type = "inputerror"
      error = "O substituto precisa ter uma conta ativa."
    }

    // Valida o escopo usando os valores exatos do Enum.
    precondition ($input.escopo == "ferias" || $input.escopo == "ausencia" || $input.escopo == "documento" || $input.escopo == "desligamento" || $input.escopo == "correcao_ponto" || $input.escopo == "solicitacao_rh" || $input.escopo == "todas") {
      error_type = "inputerror"
      error = "Escopo invalido."
    }

    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data de fim nao pode ser anterior a data de inicio."
    }

    db.add delegacao_aprovacao {
      data = {
        titular_user_id     : $titular.id
        substituto_user_id    : $substituto.id
        escopo                  : $input.escopo
        data_inicio               : $input.data_inicio
        data_fim                    : $input.data_fim
        motivo                       : $input.motivo
        criado_por_user_id             : $usuario_autenticado.id
        updated_at                       : "now"
      }
    } as $delegacao_criada

    // Auditoria: criacao de delegacao.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_delegacao_aprovacao"
        recurso    : "delegacao_aprovacao"
        registro_id: $delegacao_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    mensagem  : "Delegacao criada com sucesso."
    delegacao : $delegacao_criada
  }

  guid = "conectahr-delegacoes-post-0001"
}
