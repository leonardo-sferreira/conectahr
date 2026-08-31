// Cria o pre-cadastro profissional de um colaborador.
// Operacao exclusiva de uma conta RH ativa.
// O status e aplicado pelo valor padrao configurado no banco.
// Nao cria usuario, e-mail de login ou senha.
// O nivel inicial e registrado desde a data de admissao.
query colaboradores verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text nome filters=trim|min:2|max:100
    // max:14 aceita CPF com mascara (XXX.XXX.XXX-XX); validar_cpf
    // normaliza e confere os digitos verificadores logo abaixo.
    text cpf filters=trim|min:11|max:14
    email email_pessoal filters=trim|lower
    date data_nascimento
    date data_admissao
    text telefone filters=trim
    text logradouro filters=trim
    text numero filters=trim
    text bairro filters=trim
    int cargo_id
    int departamento_id
    text tipo_contrato filters=trim
    text nivel filters=trim
    decimal salario filters=min:0
    decimal carga_horaria_semanal filters=min:1|max:60
  }

  stack {
    // Localiza o usuario que esta realizando o cadastro.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh
  
    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }
  
    // Uma conta inativa nao pode cadastrar colaboradores.
    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_rh.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil do usuario autenticado.
    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }
  
    // O pre-cadastro profissional e exclusivo do RH.
    precondition ($perfil_rh == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode cadastrar colaboradores."
    }
  
    // Valida o CPF localmente (digitos verificadores) antes de qualquer
    // outra checagem — nao consulta servico externo (item 1.8).
    function.run "ConectaHR/validar_cpf" {
      input = {cpf: $input.cpf}
    } as $resultado_cpf

    precondition ($resultado_cpf.valido) {
      error_type = "inputerror"
      error = $resultado_cpf.motivo
    }

    // Verifica se o CPF ja esta cadastrado (usando a forma normalizada).
    db.get colaborador {
      field_name = "cpf"
      field_value = $resultado_cpf.cpf_normalizado
    } as $colaborador_cpf_existente

    precondition ($colaborador_cpf_existente == null) {
      error_type = "inputerror"
      error = "Ja existe um colaborador cadastrado com este CPF."
    }
  
    // Verifica se o e-mail pessoal ja pertence a outro colaborador.
    db.get colaborador {
      field_name = "email_pessoal"
      field_value = $input.email_pessoal
    } as $colaborador_email_existente
  
    precondition ($colaborador_email_existente == null) {
      error_type = "inputerror"
      error = "Este e-mail pessoal ja pertence a outro colaborador."
    }
  
    // Localiza e valida o cargo.
    db.get cargo {
      field_name = "id"
      field_value = $input.cargo_id
    } as $cargo
  
    precondition ($cargo != null) {
      error_type = "notfound"
      error = "Cargo nao encontrado."
    }
  
    precondition ($cargo.ativo) {
      error_type = "inputerror"
      error = "Nao e possivel vincular um cargo inativo."
    }
  
    // Localiza e valida o departamento.
    db.get departamento {
      field_name = "id"
      field_value = $input.departamento_id
    } as $departamento
  
    precondition ($departamento != null) {
      error_type = "notfound"
      error = "Departamento nao encontrado."
    }
  
    precondition ($departamento.ativo) {
      error_type = "inputerror"
      error = "Nao e possivel vincular um departamento inativo."
    }
  
    // Normaliza o tipo de contrato.
    var $tipo_contrato {
      value = $input.tipo_contrato|trim|to_upper
    }
  
    // Valida os tipos de contrato permitidos.
    precondition ($tipo_contrato == "CLT" || $tipo_contrato == "PJ" || $tipo_contrato == "ESTAGIO" || $tipo_contrato == "APRENDIZ" || $tipo_contrato == "TEMPORARIO" || $tipo_contrato == "OUTRO") {
      error_type = "inputerror"
      error = "Tipo de contrato invalido."
    }
  
    // Normaliza o nivel profissional.
    var $nivel_normalizado {
      value = $input.nivel|trim|to_lower
    }
  
    // Valida os niveis configurados no Enum.
    precondition ($nivel_normalizado == "l1" || $nivel_normalizado == "l2" || $nivel_normalizado == "l3" || $nivel_normalizado == "l4" || $nivel_normalizado == "l5") {
      error_type = "inputerror"
      error = "Nivel profissional invalido. Use l1, l2, l3, l4 ou l5."
    }
  
    // Cria o registro profissional.
    db.add colaborador {
      data = {
        nome                 : $input.nome
        cpf                  : $resultado_cpf.cpf_normalizado
        email_pessoal        : $input.email_pessoal
        data_nascimento      : $input.data_nascimento
        data_admissao        : $input.data_admissao
        telefone             : $input.telefone
        logradouro           : $input.logradouro
        numero               : $input.numero
        bairro               : $input.bairro
        cargo_id             : $cargo.id
        departamento_id      : $departamento.id
        tipo_contrato        : $tipo_contrato
        nivel                : $nivel_normalizado
        nivel_desde          : $input.data_admissao
        salario              : $input.salario
        carga_horaria_semanal: $input.carga_horaria_semanal
        status               : "Ativo"
        ativo                : true
        updated_at           : "now"
      }
    } as $colaborador_criado
  }

  response = {
    sucesso      : true
    mensagem     : "Colaborador pre-cadastrado com sucesso. Agora o RH pode criar sua conta de acesso."
    colaborador  : $colaborador_criado
    cargo        : $cargo
    departamento : $departamento
    nivel        : $nivel_normalizado
    proximo_passo: "Criar o acesso pelo POST /usuarios usando o ID deste colaborador."
  }

  guid = "MLBmVyypWrDez6X3MNBTTKF-O9E"
}