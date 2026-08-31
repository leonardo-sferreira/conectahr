// Atualiza os dados pessoais de um colaborador.
// Operação exclusiva do RH.
// Não altera vínculo profissional, status ou conta de acesso.
query "colaboradores/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:100
    // max:14 aceita CPF com mascara (XXX.XXX.XXX-XX); validar_cpf
    // normaliza e confere os digitos verificadores logo abaixo.
    text cpf filters=trim|min:11|max:14
    email email_pessoal filters=trim|lower
    date data_nascimento
    text telefone filters=trim|max:20
    text cep filters=trim|max:9
    text logradouro filters=trim|max:150
    text numero filters=trim|max:20
    text complemento filters=trim|max:100
    text bairro filters=trim|max:100
    text cidade filters=trim|max:100
    text estado filters=trim|min:2|max:2
  }

  stack {
    // Localiza o usuário que está realizando a alteração.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh
  
    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Uma conta inativa não pode alterar colaboradores.
    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_rh.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil autenticado.
    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }
  
    // Somente RH pode atualizar os dados do colaborador.
    precondition ($perfil_rh == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode atualizar colaboradores."
    }
  
    // Localiza o colaborador selecionado.
    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_atual
  
    precondition ($colaborador_atual != null) {
      error_type = "notfound"
      error = "Colaborador não encontrado."
    }
  
    // Valida o CPF localmente (digitos verificadores) — item 1.8.
    function.run "ConectaHR/validar_cpf" {
      input = {cpf: $input.cpf}
    } as $resultado_cpf

    precondition ($resultado_cpf.valido) {
      error_type = "inputerror"
      error = $resultado_cpf.motivo
    }

    // Verifica se o CPF pertence a outro colaborador.
    db.get colaborador {
      field_name = "cpf"
      field_value = $resultado_cpf.cpf_normalizado
    } as $colaborador_mesmo_cpf

    precondition ($colaborador_mesmo_cpf == null || $colaborador_mesmo_cpf.id == $colaborador_atual.id) {
      error_type = "inputerror"
      error = "Este CPF já pertence a outro colaborador."
    }
  
    // Verifica se o e-mail pessoal pertence a outro colaborador.
    db.get colaborador {
      field_name = "email_pessoal"
      field_value = $input.email_pessoal
    } as $colaborador_mesmo_email
  
    precondition ($colaborador_mesmo_email == null || $colaborador_mesmo_email.id == $colaborador_atual.id) {
      error_type = "inputerror"
      error = "Este e-mail pessoal já pertence a outro colaborador."
    }
  
    // Normaliza a sigla do estado.
    var $estado_normalizado {
      value = $input.estado|trim|to_upper
    }
  
    // Atualiza somente os dados pessoais permitidos.
    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador_atual.id
      data = {
        nome           : $input.nome
        cpf            : $resultado_cpf.cpf_normalizado
        email_pessoal  : $input.email_pessoal
        data_nascimento: $input.data_nascimento
        telefone       : $input.telefone
        cep            : $input.cep
        logradouro     : $input.logradouro
        numero         : $input.numero
        complemento    : $input.complemento
        bairro         : $input.bairro
        cidade         : $input.cidade
        estado         : $estado_normalizado
        updated_at     : "now"
      }
    } as $colaborador_atualizado

    // Auditoria: alteracao cadastral pelo RH.
    db.add auditoria {
      data = {
        user_id       : $usuario_rh.id
        acao          : "alterar_cadastro_colaborador"
        recurso       : "colaborador"
        registro_id   : $colaborador_atual.id
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Dados do colaborador atualizados com sucesso."
    colaborador: $colaborador_atualizado
  }

  guid = "DASuqa7XoKz4D05m52crjD2LXr4"
}