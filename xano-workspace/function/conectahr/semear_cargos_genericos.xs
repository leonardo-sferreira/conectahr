// Niveis hierarquicos e cargos genericos de partida (pedido do usuario em 13/10/2026, para a apresentacao): a escada
// de CEO a estagio e cargos comuns a qualquer empresa, sem departamento (servem a todos). Rodar a mao (xano function
// run). So cria o que nao existe (nome comparado sem diferenca de maiusculas) e so poe nivel em cargo que esta sem;
// nao mexe no que o RH cadastrou. Salario base e referencia de exemplo, para o RH ajustar. Auditado.
function "ConectaHR/semear_cargos_genericos" {
  input {
  }

  stack {
    var $niveis_base {
      value = []
        |push:{nome: "Presidência", ordem: 1}
        |push:{nome: "Diretoria", ordem: 2}
        |push:{nome: "Head", ordem: 3}
        |push:{nome: "Gerência", ordem: 4}
        |push:{nome: "Coordenação", ordem: 5}
        |push:{nome: "Supervisão", ordem: 6}
        |push:{nome: "Especialistas e analistas", ordem: 7}
        |push:{nome: "Operacional", ordem: 8}
        |push:{nome: "Estágio e aprendizagem", ordem: 9}
    }

    var $cargos_base {
      value = []
        |push:{nome: "CEO", nivel: "Presidência", senioridade: null, salario: 35000, descricao: "Principal executivo da empresa: estrategia, resultados e lideranca da diretoria."}
        |push:{nome: "Diretor", nivel: "Diretoria", senioridade: null, salario: 25000, descricao: "Responde por uma area de negocio e pelos seus resultados."}
        |push:{nome: "Head", nivel: "Head", senioridade: null, salario: 20000, descricao: "Lidera uma area ou disciplina e os gerentes dela."}
        |push:{nome: "Gerente", nivel: "Gerência", senioridade: null, salario: 14000, descricao: "Gere uma equipe ou um setor: metas, pessoas e orcamento."}
        |push:{nome: "Coordenador", nivel: "Coordenação", senioridade: null, salario: 9000, descricao: "Coordena os processos e a rotina de uma equipe."}
        |push:{nome: "Supervisor", nivel: "Supervisão", senioridade: null, salario: 6500, descricao: "Acompanha a operacao do dia a dia e orienta a equipe."}
        |push:{nome: "Analista Júnior", nivel: "Especialistas e analistas", senioridade: "junior", salario: 3500, descricao: "Executa as atividades da area com orientacao."}
        |push:{nome: "Analista Pleno", nivel: "Especialistas e analistas", senioridade: "pleno", salario: 5500, descricao: "Executa as atividades da area com autonomia."}
        |push:{nome: "Analista Sênior", nivel: "Especialistas e analistas", senioridade: "senior", salario: 8000, descricao: "Referencia tecnica da area; apoia os mais novos."}
        |push:{nome: "Analista de Suporte (Help Desk) Júnior", nivel: "Especialistas e analistas", senioridade: "junior", salario: 3000, descricao: "Atende chamados de TI e resolve problemas de primeiro nivel."}
        |push:{nome: "Analista de Suporte (Help Desk) Pleno", nivel: "Especialistas e analistas", senioridade: "pleno", salario: 4500, descricao: "Atende chamados de TI de maior complexidade."}
        |push:{nome: "Assistente Administrativo", nivel: "Operacional", senioridade: null, salario: 2600, descricao: "Apoia as rotinas administrativas da area."}
        |push:{nome: "Auxiliar Administrativo", nivel: "Operacional", senioridade: null, salario: 2200, descricao: "Executa tarefas administrativas de apoio."}
        |push:{nome: "Atendente", nivel: "Operacional", senioridade: null, salario: 2000, descricao: "Atende clientes por telefone, chat ou presencialmente."}
        |push:{nome: "Estagiário", nivel: "Estágio e aprendizagem", senioridade: null, salario: 1800, descricao: "Estagio supervisionado (Lei 11.788/2008); a bolsa e o valor de referencia."}
        |push:{nome: "Jovem Aprendiz", nivel: "Estágio e aprendizagem", senioridade: null, salario: 1300, descricao: "Contrato de aprendizagem (CLT, arts. 428 a 433)."}
    }

    // Cargos antigos sem nivel que ganham um (nome em minusculas -> nivel).
    var $niveis_dos_antigos {
      value = {analista: "Especialistas e analistas", atendente: "Operacional", "help desk": "Operacional"}
    }

    // ---------- Niveis ----------
    db.query nivel_hierarquico {
      return = {type: "list"}
    } as $niveis_existentes

    var $niveis_criados {
      value = []
    }

    foreach ($niveis_base) {
      each as $nb {
        var $ja_existe_nivel {
          value = false
        }

        foreach ($niveis_existentes) {
          each as $ne {
            conditional {
              if (($ne.nome|to_lower) == ($nb.nome|to_lower)) {
                var.update $ja_existe_nivel {
                  value = true
                }
              }
            }
          }
        }

        conditional {
          if ($ja_existe_nivel == false) {
            db.add nivel_hierarquico {
              data = {nome: $nb.nome, ordem: $nb.ordem, ativo: true}
            } as $nivel_novo

            var.update $niveis_criados {
              value = $niveis_criados|push:$nb.nome
            }
          }
        }
      }
    }

    // Mapa nome do nivel (minusculas) -> id, como texto "|nome=id|": contains em lista nao funciona.
    db.query nivel_hierarquico {
      return = {type: "list"}
    } as $niveis_todos

    // ---------- Cargos ----------
    db.query cargo {
      return = {type: "list"}
    } as $cargos_existentes

    var $nomes_cargos {
      value = "|"
    }

    foreach ($cargos_existentes) {
      each as $ce {
        var.update $nomes_cargos {
          value = $nomes_cargos ~ ($ce.nome|to_lower) ~ "|"
        }
      }
    }

    var $cargos_criados {
      value = []
    }

    foreach ($cargos_base) {
      each as $cb {
        conditional {
          if (($nomes_cargos|contains:("|" ~ ($cb.nome|to_lower) ~ "|")) == false) {
            var $nivel_id {
              value = null
            }

            foreach ($niveis_todos) {
              each as $nt {
                conditional {
                  if (($nt.nome|to_lower) == ($cb.nivel|to_lower)) {
                    var.update $nivel_id {
                      value = $nt.id
                    }
                  }
                }
              }
            }

            db.add cargo {
              data = {nome: $cb.nome, descricao: $cb.descricao, salario_base: $cb.salario, senioridade: $cb.senioridade, nivel_hierarquico_id: $nivel_id, departamento_id: null, ativo: true}
            } as $cargo_novo

            var.update $cargos_criados {
              value = $cargos_criados|push:$cb.nome
            }
          }
        }
      }
    }

    // Nivel dos cargos antigos que estao sem.
    var $cargos_com_nivel {
      value = []
    }

    foreach ($cargos_existentes) {
      each as $antigo {
        var $nivel_nome_antigo {
          value = $niveis_dos_antigos|get:($antigo.nome|to_lower|trim)
        }

        conditional {
          if (($antigo.nivel_hierarquico_id == null) && ($nivel_nome_antigo != null)) {
            foreach ($niveis_todos) {
              each as $nt2 {
                conditional {
                  if (($nt2.nome|to_lower) == ($nivel_nome_antigo|to_lower)) {
                    db.edit cargo {
                      field_name = "id"
                      field_value = $antigo.id
                      data = {nivel_hierarquico_id: $nt2.id}
                    } as $cargo_com_nivel

                    var.update $cargos_com_nivel {
                      value = $cargos_com_nivel|push:$antigo.nome
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        acao      : "semear_cargos_genericos"
        recurso   : "cargo"
        valor_novo: "niveis criados=" ~ (($niveis_criados|count)|to_text) ~ "; cargos criados=" ~ (($cargos_criados|count)|to_text) ~ "; cargos com nivel=" ~ (($cargos_com_nivel|count)|to_text)
        resultado : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    niveis_criados  : $niveis_criados
    cargos_criados  : $cargos_criados
    cargos_com_nivel: $cargos_com_nivel
  }

  tags = ["conectahr"]
  guid = "conectahr-semear-cargos-genericos-0001"
}
