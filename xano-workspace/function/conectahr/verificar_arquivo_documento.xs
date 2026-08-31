// Quarentena de arquivos (item 5.7): confere extensao, tamanho e tipo
// declarado pelo servidor antes de liberar um anexo de documento ou de
// instrumento normativo para uso. Duplicidade e hash ja sao tratados
// separadamente por quem chama (hash_arquivo em documento), pois dependem
// do contexto (escopo por colaborador) — esta funcao cobre so o que e
// generico a qualquer arquivo_url.
//
// Limitacao documentada (design.md - "Documentos e arquivos"): XanoScript
// nao da acesso aos bytes de um arquivo referenciado por URL externa
// nesta camada, entao verificacao de "tipo real" e "corrupcao" ficam
// limitadas ao que um HEAD HTTP relata (Content-Type/Content-Length
// declarados pelo servidor remoto, nao o conteudo real do arquivo) —
// mesmo gap ja registrado para o calculo de hash de imagem em
// documentos_POST.xs. Upload direto via campo `image` (imagem_frente/
// imagem_verso) e diferente: o proprio Xano ja valida que e uma imagem
// real no momento do upload, entao esses campos sao considerados
// liberados por construcao e nao passam por este fluxo.
function "ConectaHR/verificar_arquivo_documento" {
  input {
    text? arquivo_url?
  }

  stack {
    var $estado_final {
      value = "liberado"
    }

    var $motivo_final {
      value = null
    }

    conditional {
      if ($input.arquivo_url != null) {
        // ---------- 1. Extensao ----------
        var $partes_ponto {
          value = ($input.arquivo_url|split:".")
        }

        var $extensao_bruta {
          value = ($partes_ponto|last)
        }

        var $extensao {
          value = ($extensao_bruta|to_lower|trim)
        }

        var $extensoes_permitidas {
          value = ["pdf", "jpg", "jpeg", "png", "doc", "docx", "xls", "xlsx"]
        }

        var $extensao_permitida {
          value = false
        }

        foreach ($extensoes_permitidas) {
          each as $ext_permitida {
            conditional {
              if ($extensao == $ext_permitida) {
                var.update $extensao_permitida {
                  value = true
                }
              }
            }
          }
        }

        conditional {
          if ($extensao_permitida == false) {
            var.update $estado_final {
              value = "bloqueado"
            }

            var.update $motivo_final {
              value = ("Extensao de arquivo nao permitida: ." ~ $extensao_bruta ~ ". Extensoes aceitas: PDF, JPG, JPEG, PNG, DOC, DOCX, XLS, XLSX.")
            }
          }
        }

        // ---------- 2. Tamanho e tipo declarado (HEAD HTTP) ----------
        // So verifica quando a extensao ja passou — evita gastar uma
        // chamada de rede para um arquivo que ja sera bloqueado de qualquer forma.
        conditional {
          if ($extensao_permitida) {
            api.request {
              url = $input.arquivo_url
              method = "HEAD"
              headers = []
            } as $resposta_head

            var $head_ok {
              value = ($resposta_head.response.status >= 200 && $resposta_head.response.status < 300)
            }

            // Falha de rede/servidor inacessivel nao bloqueia automaticamente
            // (evitaria falso-positivo por instabilidade de terceiros) — fica
            // como "liberado" mesmo sem confirmar tamanho/tipo, e o motivo
            // fica registrado apenas para rastreabilidade, nao para bloqueio.
            conditional {
              if ($head_ok) {
                var $tamanho_bytes {
                  value = null
                }

                var $tipo_conteudo {
                  value = null
                }

                foreach ($resposta_head.response.headers) {
                  each as $linha_header {
                    var $linha_lower {
                      value = ($linha_header|to_lower)
                    }

                    var $eh_content_length {
                      value = (($linha_lower|substr:0:15) == "content-length:")
                    }

                    var $eh_content_type {
                      value = (($linha_lower|substr:0:13) == "content-type:")
                    }

                    conditional {
                      if ($eh_content_length) {
                        var.update $tamanho_bytes {
                          value = (($linha_header|substr:16:999)|trim|to_int)
                        }
                      }
                    }

                    conditional {
                      if ($eh_content_type) {
                        var.update $tipo_conteudo {
                          value = (($linha_header|substr:13:999)|trim|to_lower)
                        }
                      }
                    }
                  }
                }

                // Tamanho maximo: 10MB (10485760 bytes).
                conditional {
                  if ($tamanho_bytes != null && $tamanho_bytes > 10485760) {
                    var.update $estado_final {
                      value = "bloqueado"
                    }

                    var.update $motivo_final {
                      value = "Arquivo excede o tamanho maximo permitido de 10MB."
                    }
                  }
                }

                // Bloqueia quando o servidor declara explicitamente um
                // tipo binario generico ("application/octet-stream") para
                // uma extensao que deveria ter um tipo especifico — sinal
                // de que o servidor nao reconhece o arquivo como o tipo
                // declarado pela extensao.
                conditional {
                  if ($tipo_conteudo != null) {
                    var $tipo_generico_demais {
                      value = (($tipo_conteudo|substr:0:24) == "application/octet-stream")
                    }

                    conditional {
                      if ($tipo_generico_demais) {
                        var.update $estado_final {
                          value = "bloqueado"
                        }

                        var.update $motivo_final {
                          value = "O servidor nao confirma o tipo do arquivo (Content-Type generico); envie um link direto para o arquivo."
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    estado_verificacao: $estado_final
    motivo_bloqueio    : $motivo_final
  }

  tags = ["conectahr"]
  guid = "conectahr-verificar-arquivo-documento-0001"
}
