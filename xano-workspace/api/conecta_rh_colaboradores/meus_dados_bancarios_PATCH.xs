// Permite ao usuário autenticado cadastrar/atualizar seus próprios
// dados bancários (banco, agência, conta, dígito e tipo de conta).
// RH e Admin apenas consultam esses dados (via colaboradores/{id} ou
// meu_perfil_colaborador) para fins de pagamento — este endpoint é
// de uso exclusivo do próprio colaborador, não recebe ID.
// Cada alteração gera um evento em `auditoria`.
query "meus_dados_bancarios" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text banco filters=trim|min:2|max:100
    text agencia filters=trim|min:1|max:10
    text conta filters=trim|min:1|max:20
    text digito filters=trim|min:1|max:2
    text tipo_conta filters=trim
  }

  stack {
    // Localiza o usuário identificado pelo token.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }

    // Uma conta inativa não pode atualizar dados bancários.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Localiza o colaborador vinculado ao usuário autenticado.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador

    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Não existe um colaborador vinculado a esta conta."
    }

    // Impede que um colaborador desligado altere dados bancários.
    var $status_colaborador {
      value = $colaborador.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado não pode alterar dados bancários."
    }

    // Valida o tipo de conta conforme o Enum da tabela.
    precondition ($input.tipo_conta == "corrente" || $input.tipo_conta == "poupanca") {
      error_type = "inputerror"
      error = "Tipo de conta invalido. Use corrente ou poupanca."
    }

    // Resumo dos valores anterior e novo, para a trilha de auditoria.
    var $resumo_anterior {
      value = "banco=" ~ $colaborador.banco ~ "; agencia=" ~ $colaborador.agencia ~ "; conta=" ~ $colaborador.conta ~ "; digito=" ~ $colaborador.digito ~ "; tipo_conta=" ~ $colaborador.tipo_conta
    }

    var $resumo_novo {
      value = "banco=" ~ $input.banco ~ "; agencia=" ~ $input.agencia ~ "; conta=" ~ $input.conta ~ "; digito=" ~ $input.digito ~ "; tipo_conta=" ~ $input.tipo_conta
    }

    // Atualiza somente os dados bancários.
    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador.id
      data = {
        banco     : $input.banco
        agencia   : $input.agencia
        conta     : $input.conta
        digito    : $input.digito
        tipo_conta: $input.tipo_conta
        updated_at: "now"
      }
    } as $colaborador_atualizado

    // Registra a alteração na auditoria.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "atualizar_dados_bancarios"
        recurso       : "colaborador"
        registro_id   : $colaborador.id
        valor_anterior: $resumo_anterior
        valor_novo    : $resumo_novo
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Dados bancários atualizados com sucesso."
    colaborador: $colaborador_atualizado
  }

  guid = "conectahr-meus-dados-bancarios-patch-0001"
}
