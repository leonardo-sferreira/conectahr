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
    // Contato e endereco opcionais (13/10/2026): o RH aplica um pedido de CPF ou de nome mesmo que a ficha
    // ainda nao tenha endereco. Vazio mantem o que ja esta na ficha.
    text? telefone? filters=trim|max:20
    text? cep? filters=trim|max:9
    text? logradouro? filters=trim|max:150
    text? numero? filters=trim|max:20
    text? complemento? filters=trim|max:100
    text? bairro? filters=trim|max:100
    text? cidade? filters=trim|max:100
    text? estado? filters=trim|max:2
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
  
    // Contato e endereco: o valor enviado, ou o da ficha quando vem vazio.
    var $telefone_final {
      value = ($input.telefone != null && $input.telefone != "" ? $input.telefone : $colaborador_atual.telefone)
    }

    var $cep_final {
      value = ($input.cep != null && $input.cep != "" ? $input.cep : $colaborador_atual.cep)
    }

    var $logradouro_final {
      value = ($input.logradouro != null && $input.logradouro != "" ? $input.logradouro : $colaborador_atual.logradouro)
    }

    var $numero_final {
      value = ($input.numero != null && $input.numero != "" ? $input.numero : $colaborador_atual.numero)
    }

    var $complemento_final {
      value = ($input.complemento != null ? $input.complemento : $colaborador_atual.complemento)
    }

    var $bairro_final {
      value = ($input.bairro != null && $input.bairro != "" ? $input.bairro : $colaborador_atual.bairro)
    }

    var $cidade_final {
      value = ($input.cidade != null && $input.cidade != "" ? $input.cidade : $colaborador_atual.cidade)
    }

    // Normaliza a sigla do estado; quando vem, precisa ser uma UF (comparacao em texto: contains em lista nao funciona).
    var $estado_normalizado {
      value = ($input.estado != null && $input.estado != "" ? ($input.estado|trim|to_upper) : $colaborador_atual.estado)
    }

    precondition ($estado_normalizado == null || $estado_normalizado == "" || (",AC,AL,AP,AM,BA,CE,DF,ES,GO,MA,MT,MS,MG,PA,PB,PR,PE,PI,RJ,RN,RS,RO,RR,SC,SP,SE,TO,"|contains:("," ~ $estado_normalizado ~ ","))) {
      error_type = "inputerror"
      error = "Estado invalido. Use a sigla da UF, como SP."
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
        telefone       : $telefone_final
        cep            : $cep_final
        logradouro     : $logradouro_final
        numero         : $numero_final
        complemento    : $complemento_final
        bairro         : $bairro_final
        cidade         : $cidade_final
        estado         : $estado_normalizado
        updated_at     : "now"
      }
    } as $colaborador_atualizado

    // REP-P: mudanca de nome ou CPF vai para a ARP (AFD registro tipo 5, operacao "A").
    conditional {
      if ($colaborador_atual.nome != $input.nome || $colaborador_atual.cpf != $resultado_cpf.cpf_normalizado) {
        function.run "ConectaHR/registrar_empregado_rep" {
          input = {colaborador_id: $colaborador_atual.id, operacao: "A", responsavel_user_id: $usuario_rh.id}
        } as $registro_rep_empregado
      }
    }

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

    // Aviso (parte 2 das notificacoes, 12/10/2026).
    function.run "ConectaHR/notificar" {
      input = {colaborador_id: $colaborador_atual.id, autor_user_id: $usuario_rh.id, tipo: "cadastro_atualizado", titulo: "Seu cadastro foi atualizado", mensagem: "O RH atualizou o seu cadastro. Confira em Perfil.", recurso: "colaborador", registro_id: $colaborador_atual.id}
    } as $aviso_cadastro
  }

  response = {
    sucesso    : true
    mensagem   : "Dados do colaborador atualizados com sucesso."
    colaborador: $colaborador_atualizado
  }

  guid = "DASuqa7XoKz4D05m52crjD2LXr4"
}