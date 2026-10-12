// Cadastra ou altera os dados do empregador e do REP-P (Portaria MTP 671/2021, change
// ponto-rep-p-e-ferias-clt). Somente RH ou Admin. Quando mudam os dados do empregador
// (identificador, CNO/CAEPF, razao social ou local), grava o registro tipo 2 na ARP com o
// CPF de quem alterou (Anexo IX, item 6.1). Auditado.
query "empregador" verb=PUT {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    enum tipo_identificador {
      values = ["cnpj", "cpf"]
    }

    text identificador filters=trim|max:20
    text? cno_caepf? filters=trim|max:20
    text razao_social filters=trim|min:2|max:150
    text local_prestacao filters=trim|min:2|max:100
    text? inpi_registro? filters=trim|max:17
    enum? desenvolvedor_tipo_identificador? {
      values = ["cnpj", "cpf"]
    }

    text? desenvolvedor_identificador? filters=trim|max:20
    text? desenvolvedor_nome? filters=trim|max:150
    text? desenvolvedor_email? filters=trim|max:50
    text? ptrp_nome? filters=trim|max:150
    text? ptrp_versao? filters=trim|max:8
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem alterar os dados do empregador."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $ficha_responsavel

    var $cpf_responsavel {
      value = ($ficha_responsavel != null && $ficha_responsavel.cpf != null ? $ficha_responsavel.cpf : "")
    }

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $cpf_responsavel}
    } as $cpf_responsavel_digitos

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $input.identificador}
    } as $identificador

    precondition (($input.tipo_identificador == "cnpj" && ($identificador|strlen) == 14) || ($input.tipo_identificador == "cpf" && ($identificador|strlen) == 11)) {
      error_type = "inputerror"
      error = "Informe o CNPJ com 14 digitos ou o CPF com 11."
    }

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $input.cno_caepf}
    } as $cno_caepf

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $input.desenvolvedor_identificador}
    } as $desenvolvedor_identificador

    db.query empregador {
      sort = {empregador.id: "asc"}
      return = {type: "single"}
    } as $anterior

    var $empregador_id {
      value = 0
    }

    conditional {
      if ($anterior == null) {
        db.add empregador {
          data = {
            tipo_identificador              : $input.tipo_identificador
            identificador                   : $identificador
            cno_caepf                       : (($cno_caepf|strlen) > 0 ? $cno_caepf : null)
            razao_social                    : $input.razao_social
            local_prestacao                 : $input.local_prestacao
            inpi_registro                   : $input.inpi_registro
            desenvolvedor_tipo_identificador: ($input.desenvolvedor_tipo_identificador != null ? $input.desenvolvedor_tipo_identificador : "cnpj")
            desenvolvedor_identificador     : (($desenvolvedor_identificador|strlen) > 0 ? $desenvolvedor_identificador : null)
            desenvolvedor_nome              : $input.desenvolvedor_nome
            desenvolvedor_email             : $input.desenvolvedor_email
            ptrp_nome                       : $input.ptrp_nome
            ptrp_versao                     : $input.ptrp_versao
            atualizado_por_user_id          : $usuario_autenticado.id
            updated_at                      : "now"
          }
        } as $criado

        var.update $empregador_id {
          value = $criado.id
        }
      }

      else {
        db.edit empregador {
          field_name = "id"
          field_value = $anterior.id
          data = {
            tipo_identificador              : $input.tipo_identificador
            identificador                   : $identificador
            cno_caepf                       : (($cno_caepf|strlen) > 0 ? $cno_caepf : null)
            razao_social                    : $input.razao_social
            local_prestacao                 : $input.local_prestacao
            inpi_registro                   : $input.inpi_registro
            desenvolvedor_tipo_identificador: ($input.desenvolvedor_tipo_identificador != null ? $input.desenvolvedor_tipo_identificador : "cnpj")
            desenvolvedor_identificador     : (($desenvolvedor_identificador|strlen) > 0 ? $desenvolvedor_identificador : null)
            desenvolvedor_nome              : $input.desenvolvedor_nome
            desenvolvedor_email             : $input.desenvolvedor_email
            ptrp_nome                       : $input.ptrp_nome
            ptrp_versao                     : $input.ptrp_versao
            atualizado_por_user_id          : $usuario_autenticado.id
            updated_at                      : "now"
          }
        } as $editado

        var.update $empregador_id {
          value = $editado.id
        }
      }
    }

    // Registro tipo 2 so quando mudam os dados do empregador (nao os do programa).
    var $mudou_empregador {
      value = ($anterior == null || $anterior.tipo_identificador != $input.tipo_identificador || $anterior.identificador != $identificador || $anterior.cno_caepf != (($cno_caepf|strlen) > 0 ? $cno_caepf : null) || $anterior.razao_social != $input.razao_social || $anterior.local_prestacao != $input.local_prestacao)
    }

    conditional {
      if ($mudou_empregador) {
        function.run "ConectaHR/gravar_registro_rep" {
          input = {tipo_registro: 2, cpf_responsavel: $cpf_responsavel_digitos, responsavel_user_id: $usuario_autenticado.id, dados: {tipo_identificador: ($input.tipo_identificador == "cnpj" ? "1" : "2"), identificador: $identificador, cno_caepf: $cno_caepf, razao_social: $input.razao_social, local_prestacao: $input.local_prestacao}}
        } as $registro_rep
      }
    }

    db.get empregador {
      field_name = "id"
      field_value = $empregador_id
    } as $empregador

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : ($anterior == null ? "cadastrar_empregador" : "alterar_empregador")
        recurso       : "empregador"
        registro_id   : $empregador_id
        valor_anterior: ($anterior != null ? ("razao_social=" ~ $anterior.razao_social ~ "; identificador=" ~ $anterior.identificador) : "")
        valor_novo    : "razao_social=" ~ $input.razao_social ~ "; identificador=" ~ $identificador ~ "; registro_tipo_2=" ~ ($mudou_empregador ? "sim" : "nao")
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {sucesso: true, empregador: $empregador, registro_tipo_2: $mudou_empregador}

  guid = "conectahr-empregador-put-0001"
}
