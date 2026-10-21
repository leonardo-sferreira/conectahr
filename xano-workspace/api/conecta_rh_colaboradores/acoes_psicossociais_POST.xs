// Cria uma acao do plano de riscos psicossociais (NR-1; change riscos-psicossociais, D3): a avaliacao, o setor
// (0 = empresa inteira), a dimensao, o nivel do risco, a medida, o responsavel e o prazo. Auditado. So RH e Admin.
query "acoes_psicossociais" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int pesquisa_id
    int? departamento_id?
    text dimensao filters=trim|max:60
    text? nivel_risco? filters=trim|lower
    text medida filters=trim|max:1000
    text responsavel filters=trim|max:150
    date prazo
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.get pesquisa_clima {
      field_name = "id"
      field_value = $input.pesquisa_id
    } as $pesquisa

    precondition (($pesquisa != null) && ($pesquisa.tipo == "psicossocial")) {
      error_type = "notfound"
      error = "Avaliacao psicossocial nao encontrada."
    }

    precondition ((($input.dimensao|strlen) >= 3) && (($input.medida|strlen) >= 10) && (($input.responsavel|strlen) >= 2)) {
      error_type = "inputerror"
      error = "Informe a dimensao, a medida (pelo menos 10 caracteres) e o responsavel."
    }

    var $nivel {
      value = (($input.nivel_risco == null) || ($input.nivel_risco == "")) ? null : $input.nivel_risco
    }

    precondition (($nivel == null) || ($nivel == "baixo") || ($nivel == "moderado") || ($nivel == "alto")) {
      error_type = "inputerror"
      error = "Nivel invalido. Use baixo, moderado ou alto."
    }

    var $departamento_texto {
      value = $input.departamento_id|to_text
    }

    var $departamento_final {
      value = ($departamento_texto == "") ? 0 : $input.departamento_id
    }

    db.add acao_psicossocial {
      data = {
        pesquisa_clima_id : $pesquisa.id
        departamento_id   : $departamento_final
        dimensao          : $input.dimensao
        nivel_risco       : $nivel
        medida            : $input.medida
        responsavel       : $input.responsavel
        prazo             : $input.prazo
        status            : "planejada"
        criado_por_user_id: $usuario_autenticado.id
        updated_at        : "now"
      }
    } as $acao

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_acao_psicossocial"
        recurso    : "acao_psicossocial"
        registro_id: $acao.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Acao criada."
    acao    : $acao
  }

  guid = "conectahr-acoes-psicossociais-post-0001"
}
