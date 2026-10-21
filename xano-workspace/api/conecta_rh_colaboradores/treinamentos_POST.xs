// Cria um treinamento no catalogo (change treinamentos-obrigatorios, D2): nome, categoria, carga horaria,
// validade em meses (0 = sem validade), se e obrigatorio e para quem (todos ou departamentos, como ",1,4,").
// Auditado. So RH e Admin.
query "treinamentos" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text nome filters=trim
    text? descricao? filters=trim|max:1000
    text categoria filters=trim|lower
    int carga_horas
    int validade_meses
    bool obrigatorio
    text publico filters=trim|lower
    text? departamento_ids? filters=trim|max:500
    text? video_drive_id? filters=trim|max:100
    int? video_duracao?
    int? video_percentual_minimo?
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

    precondition ((($input.nome|strlen) >= 3) && (($input.nome|strlen) <= 200)) {
      error_type = "inputerror"
      error = "O nome precisa ter de 3 a 200 caracteres."
    }

    var $categoria_agulha {
      value = "," ~ $input.categoria ~ ","
    }

    precondition (",legal,seguranca,compliance,integracao,desenvolvimento,"|contains:$categoria_agulha) {
      error_type = "inputerror"
      error = "Categoria invalida."
    }

    precondition (($input.validade_meses >= 0) && ($input.validade_meses <= 120) && ($input.carga_horas >= 0) && ($input.carga_horas <= 1000)) {
      error_type = "inputerror"
      error = "Validade de 0 a 120 meses e carga horaria de 0 a 1000 horas."
    }

    precondition (($input.publico == "todos") || ($input.publico == "departamentos")) {
      error_type = "inputerror"
      error = "Publico invalido. Use todos ou departamentos."
    }

    var $departamentos_final {
      value = ($input.publico == "todos") ? null : (($input.departamento_ids == null) ? "" : $input.departamento_ids)
    }

    precondition (($input.publico == "todos") || (($departamentos_final|strlen) >= 3)) {
      error_type = "inputerror"
      error = "Escolha pelo menos um departamento."
    }

    var $video_final {
      value = (($input.video_drive_id == null) || ($input.video_drive_id == "")) ? null : $input.video_drive_id
    }

    var $duracao_final {
      value = ($video_final == null) ? 0 : (($input.video_duracao == null) ? 0 : $input.video_duracao)
    }

    var $percentual_final {
      value = ($input.video_percentual_minimo == null) ? 95 : $input.video_percentual_minimo
    }

    precondition (($video_final == null) || ((($video_final|strlen) >= 10) && (($video_final|strlen) <= 100) && (($video_final|contains:"/") == false) && (($video_final|contains:"?") == false) && (($video_final|contains:"&") == false) && (($video_final|contains:" ") == false))) {
      error_type = "inputerror"
      error = "Link do video invalido. Cole o link de compartilhamento do Google Drive."
    }

    precondition (($video_final == null) || (($duracao_final >= 10) && ($duracao_final <= 36000))) {
      error_type = "inputerror"
      error = "Duracao do video invalida (de 10 segundos a 10 horas)."
    }

    precondition (($percentual_final >= 50) && ($percentual_final <= 100)) {
      error_type = "inputerror"
      error = "O minimo assistido vai de 50% a 100%."
    }

    db.add treinamento {
      data = {
        nome              : $input.nome
        descricao         : $input.descricao
        categoria         : $input.categoria
        carga_horas       : $input.carga_horas
        validade_meses    : $input.validade_meses
        obrigatorio       : $input.obrigatorio
        publico           : $input.publico
        departamento_ids  : $departamentos_final
        video_drive_id    : $video_final
        video_duracao     : $duracao_final
        video_percentual_minimo: $percentual_final
        ativo             : true
        criado_por_user_id: $usuario_autenticado.id
        updated_at        : "now"
      }
    } as $treinamento

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_treinamento"
        recurso    : "treinamento"
        registro_id: $treinamento.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Treinamento criado."
    treinamento: $treinamento
  }

  guid = "conectahr-treinamentos-post-0001"
}
