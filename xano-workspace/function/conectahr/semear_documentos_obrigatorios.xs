// Documentos obrigatorios pre-definidos por tipo de contrato (change documentos-obrigatorios-por-contrato, D1 e D2;
// pesquisa de 13/10/2026). Rodar a mao (xano function run). Grava so a regra que ainda nao existe ativa para o mesmo
// documento e contrato, sem cargo nem departamento: repetir nao duplica e nao mexe no que o RH cadastrou.
// Opcional = obrigatorio false (aparece na lista do RH, mas nao gera pendencia): reservista (o sistema nao coleta
// sexo) e certidao de nascimento ou casamento. Guarda: 5 anos do desligamento; ASO, 20 anos (docs/lgpd/retencao.md).
// Autor: o primeiro ADMIN ativo ou, sem ele, o primeiro RH ativo.
function "ConectaHR/semear_documentos_obrigatorios" {
  input {
  }

  stack {
    var $regras {
      value = []
        |push:{d: "cpf", c: "CLT", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "rg", c: "CLT", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "ctps", c: "CLT", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "comprovante_residencia", c: "CLT", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "comprovante_escolaridade", c: "CLT", o: true, imin: null, imax: null, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "aso_admissional", c: "CLT", o: true, imin: null, imax: null, p: 1, r: 7300, b: "Obrigacao legal (LGPD art. 7o, II): exame admissional (CLT art. 168; NR-7)"}
        |push:{d: "titulo_eleitor", c: "CLT", o: true, imin: 18, imax: 70, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): quitacao eleitoral (Codigo Eleitoral, art. 7o)"}
        |push:{d: "certificado_reservista", c: "CLT", o: false, imin: 18, imax: 45, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): situacao militar (Lei 4.375/1964, art. 74)"}
        |push:{d: "certidao_civil", c: "CLT", o: false, imin: null, imax: null, p: 10, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): documento complementar, quando aplicavel"}
        |push:{d: "cpf", c: "TEMPORARIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "rg", c: "TEMPORARIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "ctps", c: "TEMPORARIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "comprovante_residencia", c: "TEMPORARIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "comprovante_escolaridade", c: "TEMPORARIO", o: true, imin: null, imax: null, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "aso_admissional", c: "TEMPORARIO", o: true, imin: null, imax: null, p: 1, r: 7300, b: "Obrigacao legal (LGPD art. 7o, II): exame admissional (CLT art. 168; NR-7)"}
        |push:{d: "titulo_eleitor", c: "TEMPORARIO", o: true, imin: 18, imax: 70, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): quitacao eleitoral (Codigo Eleitoral, art. 7o)"}
        |push:{d: "certificado_reservista", c: "TEMPORARIO", o: false, imin: 18, imax: 45, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): situacao militar (Lei 4.375/1964, art. 74)"}
        |push:{d: "certidao_civil", c: "TEMPORARIO", o: false, imin: null, imax: null, p: 10, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): documento complementar, quando aplicavel"}
        |push:{d: "cpf", c: "APRENDIZ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "rg", c: "APRENDIZ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "ctps", c: "APRENDIZ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "comprovante_residencia", c: "APRENDIZ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "comprovante_escolaridade", c: "APRENDIZ", o: true, imin: null, imax: null, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): admissao e registro do empregado (CLT art. 41; eSocial)"}
        |push:{d: "aso_admissional", c: "APRENDIZ", o: true, imin: null, imax: null, p: 1, r: 7300, b: "Obrigacao legal (LGPD art. 7o, II): exame admissional (CLT art. 168; NR-7)"}
        |push:{d: "titulo_eleitor", c: "APRENDIZ", o: true, imin: 18, imax: 70, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): quitacao eleitoral (Codigo Eleitoral, art. 7o)"}
        |push:{d: "certificado_reservista", c: "APRENDIZ", o: false, imin: 18, imax: 45, p: 10, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): situacao militar (Lei 4.375/1964, art. 74)"}
        |push:{d: "certidao_civil", c: "APRENDIZ", o: false, imin: null, imax: null, p: 10, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): documento complementar, quando aplicavel"}
        |push:{d: "cpf", c: "ESTAGIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): Lei 11.788/2008 (termo de compromisso, matricula e seguro)"}
        |push:{d: "rg", c: "ESTAGIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): Lei 11.788/2008 (termo de compromisso, matricula e seguro)"}
        |push:{d: "comprovante_residencia", c: "ESTAGIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): Lei 11.788/2008 (termo de compromisso, matricula e seguro)"}
        |push:{d: "comprovante_escolaridade", c: "ESTAGIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): Lei 11.788/2008 (termo de compromisso, matricula e seguro)"}
        |push:{d: "termo_compromisso_estagio", c: "ESTAGIO", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Obrigacao legal (LGPD art. 7o, II): Lei 11.788/2008 (termo de compromisso, matricula e seguro)"}
        |push:{d: "cpf", c: "PJ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): cadastro do prestador de servicos"}
        |push:{d: "rg", c: "PJ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): cadastro do prestador de servicos"}
        |push:{d: "cartao_cnpj", c: "PJ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): cadastro do prestador de servicos"}
        |push:{d: "contrato_social", c: "PJ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): cadastro do prestador de servicos"}
        |push:{d: "comprovante_residencia", c: "PJ", o: true, imin: null, imax: null, p: 5, r: 1825, b: "Execucao de contrato (LGPD art. 7o, V): cadastro do prestador de servicos"}
        |push:{d: "documentacao_responsavel_legal", c: null, o: true, imin: null, imax: 17, p: 5, r: 1825, b: "Obrigacao legal e protecao do menor (LGPD art. 14; CLT art. 439)"}
    }

    db.query user {
      return = {type: "list"}
    } as $usuarios

    var $autor_id {
      value = null
    }

    var $autor_rh_id {
      value = null
    }

    foreach ($usuarios) {
      each as $u {
        conditional {
          if ($autor_id == null && ($u.perfil|trim|to_upper) == "ADMIN" && $u.ativo) {
            var.update $autor_id {
              value = $u.id
            }
          }

          elseif ($autor_rh_id == null && ($u.perfil|trim|to_upper) == "RH" && $u.ativo) {
            var.update $autor_rh_id {
              value = $u.id
            }
          }
        }
      }
    }

    conditional {
      if ($autor_id == null) {
        var.update $autor_id {
          value = $autor_rh_id
        }
      }
    }

    precondition ($autor_id != null) {
      error_type = "standard"
      error = "Nao ha usuario ADMIN ou RH ativo para assinar as regras."
    }

    db.query documento_obrigatorio_regra {
      where = $db.documento_obrigatorio_regra.ativo == true
      return = {type: "list"}
    } as $existentes

    // Chaves ja cadastradas ("|documento:contrato|"), so das regras gerais (sem cargo nem departamento).
    var $chaves {
      value = "|"
    }

    foreach ($existentes) {
      each as $e {
        conditional {
          if ($e.cargo_id == null && $e.departamento_id == null) {
            var.update $chaves {
              value = $chaves ~ $e.tipo_documento ~ ":" ~ ($e.tipo_contrato != null ? $e.tipo_contrato : "TODOS") ~ "|"
            }
          }
        }
      }
    }

    var $criadas {
      value = []
    }

    foreach ($regras) {
      each as $r {
        var $chave_regra {
          value = $r.d ~ ":" ~ ($r.c != null ? $r.c : "TODOS")
        }

        conditional {
          if (($chaves|contains:("|" ~ $chave_regra ~ "|")) == false) {
            db.add documento_obrigatorio_regra {
              data = {
                tipo_documento         : $r.d
                tipo_contrato          : $r.c
                idade_minima           : $r.imin
                idade_maxima           : $r.imax
                exige_frente_verso     : false
                prazo_dias_para_envio  : $r.p
                obrigatorio            : $r.o
                retencao_finalidade    : "Comprovar a admissao e cumprir obrigacoes trabalhistas, previdenciarias e fiscais"
                retencao_base_legal    : $r.b
                retencao_prazo_dias    : $r.r
                retencao_evento_inicial: "desligamento"
                retencao_tratamento    : "revisao_manual"
                ativo                  : true
                criado_por_user_id     : $autor_id
                updated_at             : "now"
              }
            } as $nova_regra

            var.update $criadas {
              value = $criadas|push:$chave_regra
            }

            var.update $chaves {
              value = $chaves ~ $chave_regra ~ "|"
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id    : $autor_id
        acao       : "semear_documentos_obrigatorios"
        recurso    : "documento_obrigatorio_regra"
        valor_novo : "regras criadas=" ~ (($criadas|count)|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    criadas    : $criadas
    ja_existiam: ($regras|count) - ($criadas|count)
  }

  tags = ["conectahr"]
  guid = "conectahr-semear-documentos-obrigatorios-0001"
}
