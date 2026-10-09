// Anonimiza um colaborador (LGPD, arts. 15, 16 e 18, IV). So RH e Admin, com
// justificativa. Substitui nome, CPF, contato, endereco, data de nascimento e
// dados bancarios por marcadores, faz o mesmo no usuario vinculado e desativa o
// acesso. NADA e excluido: o historico, os indicadores (que usam ids e agregados)
// e a auditoria continuam, sem identificar a pessoa. A operacao nao tem volta.
//
// Recusa quando:
//  - o colaborador ainda nao esta Desligado;
//  - ja foi anonimizado;
//  - algum documento ainda tem prazo de guarda vigente (`retencao_ate` no futuro);
//  - ha processo em aberto (ferias pendente, solicitacao ao RH ou desligamento em andamento).
// A auditoria registra a operacao SEM os valores anteriores. A justificativa nao deve
// conter dados pessoais.
query "colaboradores/{id}/anonimizar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text justificativa filters=trim|min:5|max:500
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
      error = "Somente RH ou ADMIN podem anonimizar um colaborador."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $alvo

    precondition ($alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Ninguem anonimiza o proprio cadastro.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_do_decisor

    precondition ($colaborador_do_decisor == null || $colaborador_do_decisor.id != $alvo.id) {
      error_type = "accessdenied"
      error = "Voce nao pode anonimizar o proprio cadastro."
    }

    precondition ($alvo.anonimizado_em == null) {
      error_type = "inputerror"
      error = "Este colaborador ja foi anonimizado."
    }

    precondition ($alvo.status == "Desligado") {
      error_type = "inputerror"
      error = "So e possivel anonimizar um colaborador desligado."
    }

    // Prazo de guarda vigente: algum documento com retencao_ate no futuro.
    var $hoje_anonimizar {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    db.query documento {
      where = $db.documento.colaborador_id == $alvo.id && $db.documento.retencao_ate != null && $db.documento.retencao_ate > $hoje_anonimizar
      return = {type: "list"}
      output = ["id"]
    } as $documentos_em_guarda

    precondition (($documentos_em_guarda|count) == 0) {
      error_type = "inputerror"
      error = "Ha documentos com prazo de guarda vigente. A anonimizacao so e possivel depois do prazo."
    }

    // Processo em aberto.
    db.query ferias {
      where = $db.ferias.colaborador_id == $alvo.id && $db.ferias.status == "Pendente"
      return = {type: "list"}
      output = ["id"]
    } as $ferias_abertas

    db.query solicitacao_rh {
      where = $db.solicitacao_rh.colaborador_id == $alvo.id && ($db.solicitacao_rh.status == "recebida" || $db.solicitacao_rh.status == "em_analise")
      return = {type: "list"}
      output = ["id"]
    } as $solicitacoes_abertas

    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.colaborador_id == $alvo.id && ($db.solicitacao_desligamento.status == "pendente" || $db.solicitacao_desligamento.status == "em_analise" || $db.solicitacao_desligamento.status == "agendado")
      return = {type: "list"}
      output = ["id"]
    } as $desligamentos_abertos

    precondition ((($ferias_abertas|count) + ($solicitacoes_abertas|count) + ($desligamentos_abertos|count)) == 0) {
      error_type = "inputerror"
      error = "Ha processo em aberto para este colaborador (ferias, solicitacao ao RH ou desligamento)."
    }

    // Marcadores. O CPF precisa ter 11 caracteres e ser unico: "0000" + id com 7 digitos.
    var $id_texto {
      value = $alvo.id|to_text
    }

    var $id_preenchido {
      value = "0000000" ~ $id_texto
    }

    var $cpf_marcador {
      value = "0000" ~ ($id_preenchido|substr:(($id_preenchido|strlen) - 7):7)
    }

    var $nome_marcador {
      value = "Colaborador anonimizado #" ~ $id_texto
    }

    var $email_marcador {
      value = "anonimizado-" ~ $id_texto ~ "@anonimizado.invalid"
    }

    db.transaction {
      stack {
        db.edit colaborador {
          field_name = "id"
          field_value = $alvo.id
          data = {
            nome           : $nome_marcador
            cpf            : $cpf_marcador
            email_pessoal  : $email_marcador
            telefone       : ""
            cep            : null
            logradouro     : ""
            numero         : ""
            complemento    : null
            bairro         : ""
            cidade         : null
            estado         : null
            data_nascimento: null
            banco          : null
            agencia        : null
            conta          : null
            digito         : null
            tipo_conta     : null
            anonimizado_em : "now"
            updated_at     : "now"
          }
        } as $colaborador_anonimizado

        // Usuario vinculado: mesmos marcadores, acesso desativado e sessoes revogadas.
        conditional {
          if ($alvo.user_id != null) {
            db.edit user {
              field_name = "id"
              field_value = $alvo.user_id
              data = {
                nome      : $nome_marcador
                email     : $email_marcador
                ativo     : false
                updated_at: "now"
              }
            } as $usuario_anonimizado

            db.query sessao {
              where = $db.sessao.user_id == $alvo.user_id && $db.sessao.ativa == true
              return = {type: "list"}
            } as $sessoes_a_revogar

            foreach ($sessoes_a_revogar) {
              each as $sessao_revogavel {
                db.edit sessao {
                  field_name = "id"
                  field_value = $sessao_revogavel.id
                  data = {ativa: false, revogada_em: "now", updated_at: "now"}
                } as $sessao_revogada
              }
            }
          }
        }

        // Auditoria sem os valores anteriores.
        db.add auditoria {
          data = {
            user_id      : $usuario_autenticado.id
            acao         : "anonimizar_colaborador"
            recurso      : "colaborador"
            registro_id  : $alvo.id
            justificativa: $input.justificativa
            resultado    : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso    : true
    mensagem   : "Colaborador anonimizado."
    colaborador: {id: $alvo.id, nome: $nome_marcador, status: $alvo.status}
  }

  guid = "conectahr-colaboradores-anonimizar-post-0001"
}
