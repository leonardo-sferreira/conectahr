// Retorna os dados seguros do usuario autenticado.
// Exige token emitido pela tabela user.
// Retorna perfil, primeiro acesso e vinculo profissional.
// Nunca retorna a senha.
query "auth/me" verb=GET {
  api_group = "ConectaRH — Autenticação"
  auth = "user"

  input {
  }

  stack {
    // Localiza o usuario identificado pelo token.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $user

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
  
    // Confirma que o usuario ainda existe.
    precondition ($user != null) {
      error_type = "unauthorized"
      error = "Usuario nao encontrado."
    }
  
    // Impede que conta desativada use tokens antigos.
    precondition ($user.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Sessao vinculada ao token (extras emitidos em auth/otp/validar).
    var $sessao_id {
      value = $auth.extras.sessao_id
    }

    // Procura o colaborador vinculado a conta.
    db.get colaborador {
      field_name = "user_id"
      field_value = $user.id
    } as $colaborador
  
    // Prepara valores nulos para contas sem colaborador.
    var $colaborador_id {
      value = null
    }
  
    var $nivel {
      value = null
    }
  
    var $nivel_desde {
      value = null
    }
  
    // Preenche os dados profissionais quando existir vinculo.
    conditional {
      if ($colaborador != null) {
        var.update $colaborador_id {
          value = $colaborador.id
        }
      
        var.update $nivel {
          value = $colaborador.nivel
        }
      
        var.update $nivel_desde {
          value = $colaborador.nivel_desde
        }
      }
    }
  }

  response = {
    autenticado          : true
    id                   : $user.id
    nome                 : $user.nome
    email                : $user.email
    perfil               : $user.perfil
    ativo                : $user.ativo
    ultimo_acesso        : $user.ultimo_acesso
    senha_primeiro_acesso: $user.senha_primeiro_acesso
    colaborador_id       : $colaborador_id
    nivel                : $nivel
    nivel_desde          : $nivel_desde
    sessao_id            : $sessao_id
  }

  guid = "KxM5swM_2tmGWnc5H3D1AqHKJfk"
}