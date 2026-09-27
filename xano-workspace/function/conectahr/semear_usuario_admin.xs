// Pre-cadastro de uma conta Admin para testes do frontend (idempotente - so
// cria se ainda nao existir uma conta com o e-mail informado). Segue o mesmo
// padrao ja usado em semear_regras_contrato/semear_parametros_protegidos:
// funcao de seed rodada uma vez via `xano function run`, nao exposta como
// endpoint de API. Nao cria colaborador vinculado - so a conta de acesso
// (user), suficiente para testar login/OTP e telas restritas a RH/Admin.
function "ConectaHR/semear_usuario_admin" {
  input {
    text nome filters=trim
    email email filters=trim|lower
    text senha_temporaria filters=min:8|max:64
  }

  stack {
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $usuario_existente

    var $usuario_final {
      value = $usuario_existente
    }

    var $ja_existia {
      value = ($usuario_existente != null)
    }

    conditional {
      if ($usuario_existente == null) {
        db.add user {
          data = {
            nome                 : $input.nome
            email                : $input.email
            senha                : $input.senha_temporaria
            perfil               : "Admin"
            ativo                : true
            senha_primeiro_acesso: true
          }
        } as $usuario_criado

        var.update $usuario_final {
          value = $usuario_criado
        }
      }
    }

    // Se a conta ja existia mas nao estava com perfil Admin, so promove o
    // perfil - nunca mexe na senha de uma conta ja existente.
    conditional {
      if ($usuario_existente != null && $usuario_existente.perfil != "Admin") {
        db.edit user {
          field_name = "id"
          field_value = $usuario_existente.id
          data = {perfil: "Admin", updated_at: "now"}
        } as $usuario_promovido

        var.update $usuario_final {
          value = $usuario_promovido
        }
      }
    }
  }

  response = {
    ja_existia: $ja_existia
    usuario   : ```
      {
        id: $usuario_final.id
        nome: $usuario_final.nome
        email: $usuario_final.email
        perfil: $usuario_final.perfil
        ativo: $usuario_final.ativo
      }
      ```
  }

  tags = ["conectahr"]
  guid = "conectahr-semear-usuario-admin-0001"
}
