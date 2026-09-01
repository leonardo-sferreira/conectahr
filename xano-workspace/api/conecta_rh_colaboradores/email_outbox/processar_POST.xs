// RH/ADMIN aciona o processamento do outbox de e-mail (item 5.5). Sem
// Background Tasks neste plano Xano — disparo manual, mesmo padrao ja
// usado em desligamento agendado e vencimento de documentos. Reprocessa
// so entradas "pendente" com tentativas < max_tentativas; em falha do
// provedor, incrementa tentativas e registra o erro sem duplicar o
// envio (chave_idempotencia garante uma entrada por evento logico desde
// a criacao, nao neste endpoint).
query "email_outbox/processar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh

    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }

    precondition ($perfil_rh == "RH" || $perfil_rh == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem processar o outbox de e-mail."
    }

    db.query email_outbox {
      where = $db.email_outbox.status == "pendente"
      sort = {email_outbox.created_at: "asc"}
      return = {type: "list"}
    } as $pendentes

    var $total_enviados {
      value = 0
    }

    var $total_falhados {
      value = 0
    }

    var $total_ignorados_limite {
      value = 0
    }

    foreach ($pendentes) {
      each as $item_outbox {
        conditional {
          if ($item_outbox.tentativas >= $item_outbox.max_tentativas) {
            db.edit email_outbox {
              field_name = "id"
              field_value = $item_outbox.id
              data = {status: "falhou", updated_at: "now"}
            } as $item_marcado_falhou

            var.update $total_ignorados_limite {
              value = $total_ignorados_limite + 1
            }
          }
        }

        conditional {
          if ($item_outbox.tentativas < $item_outbox.max_tentativas) {
            // Template transacional "conectahr_outbox_generico" (id 1 —
            // ver docs/emails-templates.md), compartilhado por todos os
            // eventos assincronos deste outbox: assunto/corpo continuam
            // montados no produtor de cada evento, so o envio em si
            // passou a usar template em vez de texto puro.
            api.request {
              url = "https://api.brevo.com/v3/smtp/email"
              method = "POST"
              headers = ["Content-Type: application/json", "api-key: " ~ $env.BREVO_API_KEY]
              params = {
                to        : [{email: $item_outbox.destinatario_email, name: $item_outbox.destinatario_nome}]
                templateId: 1
                params    : {nome: $item_outbox.destinatario_nome, titulo: $item_outbox.assunto, mensagem: $item_outbox.corpo}
              }
            } as $resposta_envio

            var $envio_ok {
              value = ($resposta_envio.response.status >= 200 && $resposta_envio.response.status < 300)
            }

            conditional {
              if ($envio_ok) {
                db.edit email_outbox {
                  field_name = "id"
                  field_value = $item_outbox.id
                  data = {status: "enviado", enviado_em: "now", updated_at: "now"}
                } as $item_marcado_enviado

                var.update $total_enviados {
                  value = $total_enviados + 1
                }
              }
            }

            conditional {
              if ($envio_ok == false) {
                var $nova_tentativa {
                  value = ($item_outbox.tentativas + 1)
                }

                var $novo_status {
                  value = ($nova_tentativa >= $item_outbox.max_tentativas ? "falhou" : "pendente")
                }

                db.edit email_outbox {
                  field_name = "id"
                  field_value = $item_outbox.id
                  data = {
                    tentativas : $nova_tentativa
                    status     : $novo_status
                    ultimo_erro: ("status HTTP " ~ (($resposta_envio.response.status)|to_text))
                    updated_at : "now"
                  }
                } as $item_marcado_falha

                var.update $total_falhados {
                  value = $total_falhados + 1
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso                : true
    total_pendentes_no_lote: ($pendentes|count)
    total_enviados         : $total_enviados
    total_falhados         : $total_falhados
    total_ja_no_limite     : $total_ignorados_limite
  }

  guid = "conectahr-email-outbox-processar-post-0001"
}
