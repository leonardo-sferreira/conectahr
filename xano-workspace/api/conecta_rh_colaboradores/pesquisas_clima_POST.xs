// RH/ADMIN cria uma pesquisa de clima. As perguntas podem vir juntas em `perguntas`
// (lista de {texto, escala}; change pesquisa-clima-e-avaliacao-360, D3), numa chamada so,
// ou ser adicionadas depois via `pesquisas_clima/{id}/perguntas`, antes de a pesquisa abrir.
// escala: concordancia (1 a 5, o padrao), nps (0 a 10) ou frequencia (1 a 5, nunca a sempre).
// tipo psicossocial (change riscos-psicossociais, D1): a avaliacao de riscos da NR-1; cada pergunta
// traz a dimensao e o sentido (risco ou protecao).
query pesquisas_clima verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text titulo filters=trim|max:200
    text? descricao? filters=trim|max:1000
    date data_inicio
    date data_fim
    int? minimo_respostas? filters=min:2
    json? perguntas?
    text? tipo? filters=trim|lower
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem criar pesquisas de clima."
    }

    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data de fim nao pode ser anterior a data de inicio."
    }

    var $perguntas_entrada {
      value = ($input.perguntas == null ? [] : $input.perguntas)
    }

    precondition (($perguntas_entrada|count) <= 30) {
      error_type = "inputerror"
      error = "Use no maximo 30 perguntas por pesquisa."
    }

    // Confere as perguntas antes de gravar qualquer coisa.
    foreach ($perguntas_entrada) {
      each as $pergunta_entrada {
        var $texto_pergunta {
          value = (($pergunta_entrada|get:"texto")|to_text)|trim
        }

        var $escala_pergunta {
          value = (($pergunta_entrada|get:"escala")|to_text)|trim
        }

        precondition ((($texto_pergunta|strlen) >= 5) && (($texto_pergunta|strlen) <= 500)) {
          error_type = "inputerror"
          error = "Cada pergunta precisa ter de 5 a 500 caracteres."
        }

        precondition (($escala_pergunta == "") || ($escala_pergunta == "concordancia") || ($escala_pergunta == "nps") || ($escala_pergunta == "frequencia")) {
          error_type = "inputerror"
          error = "Escala invalida. Use concordancia, nps ou frequencia."
        }

        var $sentido_pergunta {
          value = (($pergunta_entrada|get:"sentido")|to_text)|trim
        }

        precondition (($sentido_pergunta == "") || ($sentido_pergunta == "risco") || ($sentido_pergunta == "protecao")) {
          error_type = "inputerror"
          error = "Sentido invalido. Use risco ou protecao."
        }
      }
    }

    var $tipo_final {
      value = (($input.tipo == null) || ($input.tipo == "")) ? "clima" : $input.tipo
    }

    precondition (($tipo_final == "clima") || ($tipo_final == "psicossocial")) {
      error_type = "inputerror"
      error = "Tipo invalido. Use clima ou psicossocial."
    }

    var $minimo_final {
      value = ($input.minimo_respostas != null ? $input.minimo_respostas : 5)
    }

    db.add pesquisa_clima {
      data = {
        titulo             : $input.titulo
        descricao             : $input.descricao
        data_inicio              : $input.data_inicio
        data_fim                    : $input.data_fim
        minimo_respostas               : $minimo_final
        criado_por_user_id                : $usuario_autenticado.id
        ativo                                : true
        tipo                                    : $tipo_final
        updated_at                              : "now"
      }
    } as $pesquisa_criada

    var $ordem_pergunta {
      value = 0
    }

    foreach ($perguntas_entrada) {
      each as $pergunta_nova {
        var.update $ordem_pergunta {
          value = $ordem_pergunta + 1
        }

        var $escala_nova {
          value = (($pergunta_nova|get:"escala")|to_text)|trim
        }

        var $dimensao_nova {
          value = (($pergunta_nova|get:"dimensao")|to_text)|trim
        }

        var $sentido_novo {
          value = (($pergunta_nova|get:"sentido")|to_text)|trim
        }

        db.add pergunta_clima {
          data = {
            pesquisa_clima_id: $pesquisa_criada.id
            texto            : (($pergunta_nova|get:"texto")|to_text)|trim
            ordem            : $ordem_pergunta
            escala           : ($escala_nova == "nps" ? "nps" : ($escala_nova == "frequencia" ? "frequencia" : "concordancia"))
            dimensao         : (($dimensao_nova == "") ? null : $dimensao_nova)
            sentido          : (($sentido_novo == "") ? null : $sentido_novo)
          }
        } as $pergunta_criada
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_pesquisa_clima"
        recurso    : "pesquisa_clima"
        registro_id: $pesquisa_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Pesquisa de clima criada com sucesso."
    pesquisa: $pesquisa_criada
  }

  guid = "conectahr-pesquisas-clima-post-0001"
}
