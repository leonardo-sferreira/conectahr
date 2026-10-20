// Grava a resposta de uma pergunta na etapa aberta do ciclo (change ciclo-de-metas, D3). Etapa 1:
// a meta (cria o formulario na primeira resposta e guarda o texto da pergunta); etapas 2 e 3: o que
// foi alcancado e a autoavaliacao (abaixo, dentro ou acima). So dentro da janela e antes do envio.
// Auditado sem o texto da resposta.
query "meu_ciclo_metas/{ciclo_id}/respostas" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int ciclo_id
    int pergunta_meta_id
    text? texto? filters=trim|max:2000
    text? autoavaliacao? filters=trim
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.get ciclo_metas {
      field_name = "id"
      field_value = $input.ciclo_id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de metas nao encontrado."
    }

    var $etapa_aberta {
      value = null
    }

    conditional {
      if (($ciclo.etapa1_inicio <= $hoje) && ($hoje <= $ciclo.etapa1_fim)) {
        var.update $etapa_aberta {
          value = 1
        }
      }
    }

    conditional {
      if (($ciclo.etapa2_inicio <= $hoje) && ($hoje <= $ciclo.etapa2_fim)) {
        var.update $etapa_aberta {
          value = 2
        }
      }
    }

    conditional {
      if (($ciclo.etapa3_inicio <= $hoje) && ($hoje <= $ciclo.etapa3_fim)) {
        var.update $etapa_aberta {
          value = 3
        }
      }
    }

    precondition ($etapa_aberta != null) {
      error_type = "inputerror"
      error = "Nenhuma etapa deste ciclo esta aberta agora: fora da janela, as respostas nao mudam."
    }

    var $autoavaliacao {
      value = ((($input.autoavaliacao == null) || ($input.autoavaliacao == "")) ? null : $input.autoavaliacao)
    }

    precondition (($autoavaliacao == null) || ($autoavaliacao == "abaixo") || ($autoavaliacao == "dentro") || ($autoavaliacao == "acima")) {
      error_type = "inputerror"
      error = "Autoavaliacao invalida. Use abaixo, dentro ou acima do esperado."
    }

    db.query formulario_meta {
      where = $db.formulario_meta.ciclo_metas_id == $ciclo.id && $db.formulario_meta.colaborador_id == $colaborador_autenticado.id
      return = {type: "single"}
    } as $form_existente

    precondition (($form_existente != null) || ($etapa_aberta == 1)) {
      error_type = "inputerror"
      error = "Voce nao enviou as metas na etapa 1, entao nao ha o que acompanhar nesta etapa."
    }

    var $form {
      value = $form_existente
    }

    conditional {
      if ($form_existente == null) {
        db.add formulario_meta {
          data = {ciclo_metas_id: $ciclo.id, colaborador_id: $colaborador_autenticado.id, updated_at: "now"}
        } as $form_criado

        var.update $form {
          value = $form_criado
        }
      }
    }

    precondition ((($etapa_aberta != 1) || ($form.etapa1_enviada_em == null)) && (($etapa_aberta != 2) || ($form.etapa2_enviada_em == null)) && (($etapa_aberta != 3) || ($form.etapa3_enviada_em == null))) {
      error_type = "inputerror"
      error = "Esta etapa ja foi enviada e nao pode mais mudar."
    }

    precondition (($etapa_aberta == 1) || ($form.etapa1_enviada_em != null)) {
      error_type = "inputerror"
      error = "Voce nao enviou as metas na etapa 1, entao nao ha o que acompanhar nesta etapa."
    }

    db.get pergunta_meta {
      field_name = "id"
      field_value = $input.pergunta_meta_id
    } as $pergunta

    db.query resposta_meta {
      where = $db.resposta_meta.formulario_meta_id == $form.id && $db.resposta_meta.pergunta_meta_id == $input.pergunta_meta_id
      return = {type: "single"}
    } as $resposta_existente

    precondition (($etapa_aberta != 1) || (($pergunta != null) && ($pergunta.ativa == true))) {
      error_type = "notfound"
      error = "Pergunta nao encontrada."
    }

    precondition (($etapa_aberta == 1) || ($resposta_existente != null)) {
      error_type = "inputerror"
      error = "Esta pergunta nao faz parte das suas metas deste ciclo."
    }

    var $resposta_id {
      value = ($resposta_existente != null ? $resposta_existente.id : null)
    }

    conditional {
      if (($etapa_aberta == 1) && ($resposta_existente == null)) {
        db.add resposta_meta {
          data = {formulario_meta_id: $form.id, pergunta_meta_id: $pergunta.id, pergunta_texto: $pergunta.texto, ordem: $pergunta.ordem, meta: $input.texto, updated_at: "now"}
        } as $resposta_criada

        var.update $resposta_id {
          value = $resposta_criada.id
        }
      }
    }

    conditional {
      if (($etapa_aberta == 1) && ($resposta_existente != null)) {
        db.edit resposta_meta {
          field_name = "id"
          field_value = $resposta_existente.id
          data = {meta: $input.texto, updated_at: "now"}
        } as $resposta_meta_editada
      }
    }

    conditional {
      if ($etapa_aberta == 2) {
        db.edit resposta_meta {
          field_name = "id"
          field_value = $resposta_existente.id
          data = {alcancado_etapa2: $input.texto, autoavaliacao_etapa2: $autoavaliacao, updated_at: "now"}
        } as $resposta_etapa2
      }
    }

    conditional {
      if ($etapa_aberta == 3) {
        db.edit resposta_meta {
          field_name = "id"
          field_value = $resposta_existente.id
          data = {alcancado_etapa3: $input.texto, autoavaliacao_etapa3: $autoavaliacao, updated_at: "now"}
        } as $resposta_etapa3
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "registrar_resposta_meta"
        recurso    : "formulario_meta"
        registro_id: $form.id
        valor_novo : ("etapa=" ~ ($etapa_aberta|to_text) ~ "; pergunta=" ~ ($input.pergunta_meta_id|to_text))
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso      : true
    mensagem     : "Resposta salva."
    formulario_id: $form.id
    etapa        : $etapa_aberta
    resposta_id  : $resposta_id
  }

  guid = "conectahr-meu-ciclo-metas-respostas-post-0001"
}
