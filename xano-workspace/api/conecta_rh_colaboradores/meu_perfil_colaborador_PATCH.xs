// Permite ao usuário autenticado atualizar seus próprios dados
// de contato, endereço e e-mail pessoal, sem pedido ao RH (tarefa 72).
// Não recebe ID e não altera dados profissionais,
// permissões ou o e-mail de login. Nome, CPF e data de nascimento
// continuam por solicitação de alteração cadastral.
// Cada alteração gera um evento em `auditoria`, com os valores mascarados.
query meu_perfil_colaborador verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text email_pessoal filters=trim|max:255
    text telefone filters=trim|max:20
    text cep filters=trim|max:9
    text logradouro filters=trim|max:150
    text numero filters=trim|max:20
    text? complemento? filters=trim|max:100
    text bairro filters=trim|max:100
    text cidade filters=trim|max:100
    text estado filters=trim|min:2|max:2
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
  
    // Uma conta inativa não pode atualizar o perfil.
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
  
    // Impede que um colaborador desligado altere o perfil.
    var $status_colaborador {
      value = $colaborador.status|trim|to_upper
    }
  
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado não pode alterar o perfil."
    }
  
    // Normaliza o e-mail pessoal.
    var $email_pessoal_normalizado {
      value = $input.email_pessoal|trim|to_lower
    }

    var $email_partes {
      value = $email_pessoal_normalizado|split:"@"
    }

    precondition (($email_partes|count) == 2 && ($email_partes|first|strlen) > 0 && ($email_partes|last|contains:".")) {
      error_type = "inputerror"
      error = "Informe um e-mail pessoal valido."
    }

    // Telefone e CEP: guarda so os digitos, caractere por caractere
    // (regex_replace nao esta disponivel de forma confiavel neste workspace).
    // Telefone (10 ou 11 digitos, com DDD) e numero do endereco (1 a 10 digitos): so numeros
    // (pedido do usuario, 20/10/2026). O complemento guarda o resto ("casa B", "apto 12").
    function.run "ConectaHR/somente_digitos" {
      input = {texto: $input.telefone}
    } as $telefone_so_digitos

    precondition ((($telefone_so_digitos == $input.telefone) && ((($telefone_so_digitos|strlen) == 10) || (($telefone_so_digitos|strlen) == 11)))) {
      error_type = "inputerror"
      error = "Informe o telefone so com numeros, com DDD (10 ou 11 digitos)."
    }

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $input.numero}
    } as $numero_so_digitos

    precondition ((($numero_so_digitos == $input.numero) && (($numero_so_digitos|strlen) >= 1) && (($numero_so_digitos|strlen) <= 10))) {
      error_type = "inputerror"
      error = "O numero do endereco aceita so numeros. Use o complemento para letras (ex.: casa B)."
    }

    var $telefone_caracteres {
      value = $input.telefone|split:""
    }

    var $telefone_digitos {
      value = ""
    }

    foreach ($telefone_caracteres) {
      each as $caractere {
        conditional {
          if ("0123456789"|contains:$caractere) {
            var.update $telefone_digitos {
              value = $telefone_digitos ~ $caractere
            }
          }
        }
      }
    }

    precondition (($telefone_digitos|strlen) == 10 || ($telefone_digitos|strlen) == 11) {
      error_type = "inputerror"
      error = "Informe o telefone com DDD (10 ou 11 digitos)."
    }

    var $cep_caracteres {
      value = $input.cep|split:""
    }

    var $cep_digitos {
      value = ""
    }

    foreach ($cep_caracteres) {
      each as $caractere {
        conditional {
          if ("0123456789"|contains:$caractere) {
            var.update $cep_digitos {
              value = $cep_digitos ~ $caractere
            }
          }
        }
      }
    }

    precondition (($cep_digitos|strlen) == 8) {
      error_type = "inputerror"
      error = "Informe o CEP com 8 digitos."
    }

    var $cep_formatado {
      value = ($cep_digitos|substr:0:5) ~ "-" ~ ($cep_digitos|substr:5:3)
    }

    precondition (($input.logradouro|strlen) > 0 && ($input.numero|strlen) > 0 && ($input.bairro|strlen) > 0 && ($input.cidade|strlen) > 0) {
      error_type = "inputerror"
      error = "Preencha logradouro, numero, bairro e cidade."
    }

    // Verifica se o e-mail pessoal está vinculado
    // a outro colaborador.
    db.get colaborador {
      field_name = "email_pessoal"
      field_value = $email_pessoal_normalizado
    } as $colaborador_mesmo_email
  
    precondition ($colaborador_mesmo_email == null || $colaborador_mesmo_email.id == $colaborador.id) {
      error_type = "inputerror"
      error = "Este e-mail pessoal já pertence a outro colaborador."
    }
  
    // Normaliza a sigla do estado.
    var $estado_normalizado {
      value = $input.estado|trim|to_upper
    }

    precondition (",AC,AL,AP,AM,BA,CE,DF,ES,GO,MA,MT,MS,MG,PA,PB,PR,PE,PI,RJ,RN,RS,RO,RR,SC,SP,SE,TO,"|contains:("," ~ $estado_normalizado ~ ",")) {
      error_type = "inputerror"
      error = "Estado (UF) invalido."
    }

    // Resumo dos valores anterior e novo, para a trilha de auditoria. Tudo entra
    // MASCARADO (LGPD): do telefone so os 4 ultimos digitos, do e-mail a primeira
    // letra e o dominio, e do endereco so a cidade e a UF.
    var $telefone_anterior_texto {
      value = ($colaborador.telefone != null ? ($colaborador.telefone|to_text) : "")
    }

    var $tamanho_telefone_anterior {
      value = $telefone_anterior_texto|strlen
    }

    var $telefone_anterior_mascarado {
      value = ($tamanho_telefone_anterior > 4 ? ("****" ~ ($telefone_anterior_texto|substr:($tamanho_telefone_anterior - 4):4)) : "****")
    }

    var $telefone_novo_mascarado {
      value = "****" ~ ($telefone_digitos|substr:(($telefone_digitos|strlen) - 4):4)
    }

    var $email_anterior_texto {
      value = ($colaborador.email_pessoal != null ? ($colaborador.email_pessoal|to_text) : "")
    }

    var $email_anterior_mascarado {
      value = (($email_anterior_texto|strlen) > 0 ? (($email_anterior_texto|substr:0:1) ~ "***@" ~ ($email_anterior_texto|split:"@"|last)) : "")
    }

    var $email_novo_mascarado {
      value = ($email_pessoal_normalizado|substr:0:1) ~ "***@" ~ ($email_partes|last)
    }

    var $resumo_anterior {
      value = "telefone=" ~ $telefone_anterior_mascarado ~ "; email_pessoal=" ~ $email_anterior_mascarado ~ "; endereco=****, " ~ $colaborador.cidade ~ "/" ~ $colaborador.estado
    }

    var $resumo_novo {
      value = "telefone=" ~ $telefone_novo_mascarado ~ "; email_pessoal=" ~ $email_novo_mascarado ~ "; endereco=****, " ~ $input.cidade ~ "/" ~ $estado_normalizado
    }

    // Atualiza somente contato, e-mail pessoal e endereço.
    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador.id
      data = {
        email_pessoal: $email_pessoal_normalizado
        telefone     : $telefone_digitos
        cep          : $cep_formatado
        logradouro   : $input.logradouro
        numero       : $input.numero
        complemento  : $input.complemento
        bairro       : $input.bairro
        cidade       : $input.cidade
        estado       : $estado_normalizado
        updated_at   : "now"
      }
    } as $colaborador_atualizado

    // Registra a alteração na auditoria.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "atualizar_contato_endereco"
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
    mensagem   : "Contato e endereco atualizados."
    colaborador: {email_pessoal: $colaborador_atualizado.email_pessoal, telefone: $colaborador_atualizado.telefone, cep: $colaborador_atualizado.cep, logradouro: $colaborador_atualizado.logradouro, numero: $colaborador_atualizado.numero, complemento: $colaborador_atualizado.complemento, bairro: $colaborador_atualizado.bairro, cidade: $colaborador_atualizado.cidade, estado: $colaborador_atualizado.estado}
  }

  guid = "6LiXzx5ZafLSgssXK-8V77bkg1Y"
}