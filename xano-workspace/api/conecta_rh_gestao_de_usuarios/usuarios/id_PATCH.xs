// Atualiza os dados básicos de uma conta de usuário.
// Não altera senha, perfil, status ativo ou vínculo com colaborador.
query "usuarios/{id}" verb=PATCH {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:100
    email email filters=trim|lower
  }

  stack {
    // Localiza o usuário que está fazendo a alteração.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
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
  
    // Impede o uso por contas desativadas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil de quem está realizando a operação.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem administrar usuários.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para alterar usuários."
    }
  
    // Localiza a conta que será alterada.
    db.get user {
      field_name = "id"
      field_value = $input.id
    } as $usuario_alvo
  
    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }
  
    // Normaliza o perfil da conta que será alterada.
    var $perfil_alvo {
      value = $usuario_alvo.perfil|trim|to_upper
    }
  
    // O RH pode editar somente contas de colaboradores.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_alvo == "COLABORADOR") {
      error_type = "accessdenied"
      error = "O RH pode alterar somente contas de colaboradores."
    }
  
    // Verifica se o novo e-mail já pertence a outra conta.
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $usuario_email_existente
  
    precondition ($usuario_email_existente == null || $usuario_email_existente.id == $usuario_alvo.id) {
      error_type = "inputerror"
      error = "Este e-mail já está vinculado a outra conta."
    }
  
    // Atualiza somente os dados permitidos.
    db.edit user {
      field_name = "id"
      field_value = $usuario_alvo.id
      data = {nome: $input.nome, email: $input.email}
    } as $usuario_atualizado

    // Troca de e-mail: alerta o titular no e-mail anterior, sem informar o
    // novo endereco, para que uma troca indevida (seguida de redefinicao de
    // senha) nao passe despercebida.
    conditional {
      if ($input.email != $usuario_alvo.email) {
        // Instante real (com milissegundos) para a chave ser unica por evento: com
        // (now|to_text) a chave virava o texto literal "now" e o 2o alerta da mesma
        // conta violava o indice unico de email_outbox (HTTP 500).
        var $instante_alerta {
          value = now|format_timestamp:"YmdHisv":"UTC"
        }

        db.add email_outbox {
          data = {
            destinatario_email: $usuario_alvo.email
            destinatario_nome : $usuario_alvo.nome
            assunto           : "ConectaRH - O e-mail de acesso da sua conta foi alterado"
            corpo             : "Ola " ~ $usuario_alvo.nome ~ ",\n\nO e-mail de acesso da sua conta no ConectaRH foi alterado pelo RH. A partir de agora, este endereco nao recebe mais os codigos de acesso.\n\nSe voce nao pediu essa alteracao, procure o RH imediatamente.\n\nEste e um aviso automatico de seguranca."
            chave_idempotencia: ("alerta_troca_email_" ~ ($usuario_alvo.id|to_text) ~ "_" ~ $instante_alerta)
          }
        } as $alerta_troca_email
      }
    }

    // Localiza o colaborador vinculado à conta.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_atualizado.id
    } as $colaborador

    // E-mail na auditoria vai MASCARADO (LGPD): primeira letra e dominio.
    var $email_anterior_partes {
      value = $usuario_alvo.email|split:"@"
    }

    var $email_anterior_mascarado {
      value = (($usuario_alvo.email|substr:0:1) ~ "***@" ~ ($email_anterior_partes|last))
    }

    var $email_novo_partes {
      value = $usuario_atualizado.email|split:"@"
    }

    var $email_novo_mascarado {
      value = (($usuario_atualizado.email|substr:0:1) ~ "***@" ~ ($email_novo_partes|last))
    }

    // Auditoria: atualizacao de conta de usuario (item 7.11).
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "atualizar_usuario"
        recurso       : "user"
        registro_id   : $usuario_alvo.id
        valor_anterior: ("nome=" ~ $usuario_alvo.nome ~ "; email=" ~ $email_anterior_mascarado)
        valor_novo    : ("nome=" ~ $usuario_atualizado.nome ~ "; email=" ~ $email_novo_mascarado)
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Usuário atualizado com sucesso."
    usuario : ```
        {
          id: $usuario_atualizado.id
          nome: $usuario_atualizado.nome
          email: $usuario_atualizado.email
          perfil: $usuario_atualizado.perfil
          ativo: $usuario_atualizado.ativo
          senha_primeiro_acesso: $usuario_atualizado.senha_primeiro_acesso
          colaborador_id: ($colaborador != null ? $colaborador.id : null)
        }
      ```
  }

  guid = "q65ipgx5I1IosmXvSNu4SUltcfA"
}