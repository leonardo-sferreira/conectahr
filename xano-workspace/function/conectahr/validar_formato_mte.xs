// Valida o formato dos tres identificadores do Sistema Mediador/MTE
// (item 4.16), sem regex — regex_replace/regex_get_all_matches nao
// funcionam de forma confiavel neste workspace Xano (mesma limitacao
// documentada em validar_cpf.xs). Verifica posicao a posicao via
// split:"" + foreach, comparando classes de caractere.
//
// tipo == "mediador": numero_solicitacao_mediador, formato MR seguido
//   de 5 ou 6 digitos, "/", 4 digitos (ex.: MR12345/2026).
// tipo == "registro_mte": numero_registro_mte, formato 2 letras
//   maiusculas, 6 digitos, "/", 4 digitos (ex.: SP123456/2026).
// tipo == "processo_mte": numero_processo_mte, formato 5 digitos, ".",
//   6 digitos, "/", 4 digitos, "-", 2 digitos (ex.: 12345.123456/2026-01).
function "ConectaHR/validar_formato_mte" {
  input {
    text valor
    text tipo
  }

  stack {
    var $valido {
      value = true
    }

    var $motivo {
      value = ""
    }

    var $tamanho {
      value = ($input.valor|strlen)
    }

    // ---------- mediador: MR + 5-6 digitos + "/" + 4 digitos ----------
    conditional {
      if ($input.tipo == "mediador") {
        var $prefixo_mediador {
          value = ($input.valor|substr:0:2)
        }

        var $formato_base_mediador {
          value = ($prefixo_mediador == "MR" && ($tamanho == 12 || $tamanho == 13))
        }

        conditional {
          if ($formato_base_mediador == false) {
            var.update $valido {
              value = false
            }

            var.update $motivo {
              value = "numero_solicitacao_mediador deve seguir o formato MR seguido de 5 ou 6 digitos, barra e 4 digitos (ex.: MR12345/2026)."
            }
          }
        }

        conditional {
          if ($formato_base_mediador) {
            var $qtd_digitos_meio_mediador {
              value = ($tamanho == 12 ? 5 : 6)
            }

            var $segmento_digitos_mediador {
              value = ($input.valor|substr:2:$qtd_digitos_meio_mediador)
            }

            var $indice_barra_mediador {
              value = (2 + $qtd_digitos_meio_mediador)
            }

            var $indice_ano_mediador {
              value = (3 + $qtd_digitos_meio_mediador)
            }

            var $barra_mediador {
              value = ($input.valor|substr:$indice_barra_mediador:1)
            }

            var $segmento_ano_mediador {
              value = ($input.valor|substr:$indice_ano_mediador:4)
            }

            var $chars_meio_mediador {
              value = $segmento_digitos_mediador|split:""
            }

            var $meio_todos_digitos_mediador {
              value = true
            }

            foreach ($chars_meio_mediador) {
              each as $c_meio {
                var $eh_digito_meio {
                  value = ($c_meio == "0" || $c_meio == "1" || $c_meio == "2" || $c_meio == "3" || $c_meio == "4" || $c_meio == "5" || $c_meio == "6" || $c_meio == "7" || $c_meio == "8" || $c_meio == "9")
                }

                conditional {
                  if ($eh_digito_meio == false) {
                    var.update $meio_todos_digitos_mediador {
                      value = false
                    }
                  }
                }
              }
            }

            var $chars_ano_mediador {
              value = $segmento_ano_mediador|split:""
            }

            var $ano_todos_digitos_mediador {
              value = true
            }

            foreach ($chars_ano_mediador) {
              each as $c_ano {
                var $eh_digito_ano {
                  value = ($c_ano == "0" || $c_ano == "1" || $c_ano == "2" || $c_ano == "3" || $c_ano == "4" || $c_ano == "5" || $c_ano == "6" || $c_ano == "7" || $c_ano == "8" || $c_ano == "9")
                }

                conditional {
                  if ($eh_digito_ano == false) {
                    var.update $ano_todos_digitos_mediador {
                      value = false
                    }
                  }
                }
              }
            }

            conditional {
              if ($barra_mediador != "/" || $meio_todos_digitos_mediador == false || $ano_todos_digitos_mediador == false) {
                var.update $valido {
                  value = false
                }

                var.update $motivo {
                  value = "numero_solicitacao_mediador deve seguir o formato MR seguido de 5 ou 6 digitos, barra e 4 digitos (ex.: MR12345/2026)."
                }
              }
            }
          }
        }
      }
    }

    // ---------- registro_mte: 2 letras + 6 digitos + "/" + 4 digitos ----------
    conditional {
      if ($input.tipo == "registro_mte") {
        conditional {
          if ($tamanho != 13) {
            var.update $valido {
              value = false
            }

            var.update $motivo {
              value = "numero_registro_mte deve seguir o formato 2 letras maiusculas, 6 digitos, barra e 4 digitos (ex.: SP123456/2026)."
            }
          }
        }

        conditional {
          if ($tamanho == 13) {
            var $letras_registro {
              value = ($input.valor|substr:0:2)
            }

            var $digitos_registro {
              value = ($input.valor|substr:2:6)
            }

            var $barra_registro {
              value = ($input.valor|substr:8:1)
            }

            var $ano_registro {
              value = ($input.valor|substr:9:4)
            }

            var $chars_letras_registro {
              value = $letras_registro|split:""
            }

            var $letras_validas_registro {
              value = true
            }

            foreach ($chars_letras_registro) {
              each as $c_letra {
                var $eh_maiuscula_registro {
                  value = ($c_letra == "A" || $c_letra == "B" || $c_letra == "C" || $c_letra == "D" || $c_letra == "E" || $c_letra == "F" || $c_letra == "G" || $c_letra == "H" || $c_letra == "I" || $c_letra == "J" || $c_letra == "K" || $c_letra == "L" || $c_letra == "M" || $c_letra == "N" || $c_letra == "O" || $c_letra == "P" || $c_letra == "Q" || $c_letra == "R" || $c_letra == "S" || $c_letra == "T" || $c_letra == "U" || $c_letra == "V" || $c_letra == "W" || $c_letra == "X" || $c_letra == "Y" || $c_letra == "Z")
                }

                conditional {
                  if ($eh_maiuscula_registro == false) {
                    var.update $letras_validas_registro {
                      value = false
                    }
                  }
                }
              }
            }

            var $chars_digitos_registro {
              value = $digitos_registro|split:""
            }

            var $digitos_validos_registro {
              value = true
            }

            foreach ($chars_digitos_registro) {
              each as $c_dig {
                var $eh_digito_registro {
                  value = ($c_dig == "0" || $c_dig == "1" || $c_dig == "2" || $c_dig == "3" || $c_dig == "4" || $c_dig == "5" || $c_dig == "6" || $c_dig == "7" || $c_dig == "8" || $c_dig == "9")
                }

                conditional {
                  if ($eh_digito_registro == false) {
                    var.update $digitos_validos_registro {
                      value = false
                    }
                  }
                }
              }
            }

            var $chars_ano_registro {
              value = $ano_registro|split:""
            }

            var $ano_valido_registro {
              value = true
            }

            foreach ($chars_ano_registro) {
              each as $c_ano_reg {
                var $eh_digito_ano_registro {
                  value = ($c_ano_reg == "0" || $c_ano_reg == "1" || $c_ano_reg == "2" || $c_ano_reg == "3" || $c_ano_reg == "4" || $c_ano_reg == "5" || $c_ano_reg == "6" || $c_ano_reg == "7" || $c_ano_reg == "8" || $c_ano_reg == "9")
                }

                conditional {
                  if ($eh_digito_ano_registro == false) {
                    var.update $ano_valido_registro {
                      value = false
                    }
                  }
                }
              }
            }

            conditional {
              if ($letras_validas_registro == false || $digitos_validos_registro == false || $barra_registro != "/" || $ano_valido_registro == false) {
                var.update $valido {
                  value = false
                }

                var.update $motivo {
                  value = "numero_registro_mte deve seguir o formato 2 letras maiusculas, 6 digitos, barra e 4 digitos (ex.: SP123456/2026)."
                }
              }
            }
          }
        }
      }
    }

    // ---------- processo_mte: 5 digitos + "." + 6 digitos + "/" + 4 digitos + "-" + 2 digitos ----------
    conditional {
      if ($input.tipo == "processo_mte") {
        conditional {
          if ($tamanho != 20) {
            var.update $valido {
              value = false
            }

            var.update $motivo {
              value = "numero_processo_mte deve seguir o formato 5 digitos, ponto, 6 digitos, barra, 4 digitos, traco e 2 digitos (ex.: 12345.123456/2026-01)."
            }
          }
        }

        conditional {
          if ($tamanho == 20) {
            var $bloco1_processo {
              value = ($input.valor|substr:0:5)
            }

            var $ponto_processo {
              value = ($input.valor|substr:5:1)
            }

            var $bloco2_processo {
              value = ($input.valor|substr:6:6)
            }

            var $barra_processo {
              value = ($input.valor|substr:12:1)
            }

            var $bloco3_processo {
              value = ($input.valor|substr:13:4)
            }

            var $traco_processo {
              value = ($input.valor|substr:17:1)
            }

            var $bloco4_processo {
              value = ($input.valor|substr:18:2)
            }

            var $todos_blocos_texto_processo {
              value = ($bloco1_processo ~ $bloco2_processo ~ $bloco3_processo ~ $bloco4_processo)
            }

            var $chars_blocos_processo {
              value = $todos_blocos_texto_processo|split:""
            }

            var $blocos_validos_processo {
              value = true
            }

            foreach ($chars_blocos_processo) {
              each as $c_proc {
                var $eh_digito_processo {
                  value = ($c_proc == "0" || $c_proc == "1" || $c_proc == "2" || $c_proc == "3" || $c_proc == "4" || $c_proc == "5" || $c_proc == "6" || $c_proc == "7" || $c_proc == "8" || $c_proc == "9")
                }

                conditional {
                  if ($eh_digito_processo == false) {
                    var.update $blocos_validos_processo {
                      value = false
                    }
                  }
                }
              }
            }

            conditional {
              if ($blocos_validos_processo == false || $ponto_processo != "." || $barra_processo != "/" || $traco_processo != "-") {
                var.update $valido {
                  value = false
                }

                var.update $motivo {
                  value = "numero_processo_mte deve seguir o formato 5 digitos, ponto, 6 digitos, barra, 4 digitos, traco e 2 digitos (ex.: 12345.123456/2026-01)."
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    valido: $valido
    motivo: $motivo
  }

  tags = ["conectahr"]
  guid = "conectahr-validar-formato-mte-0001"
}
