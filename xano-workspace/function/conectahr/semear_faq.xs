// Primeiros artigos da FAQ (12/10/2026, pedido do usuario), com as regras que o ConectaRH ja aplica.
// Rodar a mao (xano function run); grava so os titulos que ainda nao existem, entao repetir nao
// duplica e nao mexe no que o RH escreveu. Autor: o primeiro ADMIN ativo ou, sem ele, o primeiro RH ativo.
function "ConectaHR/semear_faq" {
  input {
  }

  stack {
    var $artigos {
      value = []
        |push:{categoria: "ferias", titulo: "Quantos dias de férias eu tenho?", conteudo: "Pela CLT, 30 dias corridos a cada 12 meses de trabalho (o período aquisitivo). A tela Férias mostra os números do seu contrato."}
        |push:{categoria: "ferias", titulo: "Posso dividir minhas férias?", conteudo: "Sim, em até 3 períodos: um deles com pelo menos 14 dias e os outros com pelo menos 5 dias corridos cada (CLT, art. 134)."}
        |push:{categoria: "ferias", titulo: "Com quanto tempo de antecedência peço férias?", conteudo: "A antecedência mínima depende do seu contrato e aparece no pedido, na tela Férias. Peça com folga para o seu gestor se organizar."}
        |push:{categoria: "ferias", titulo: "Posso cancelar um pedido de férias?", conteudo: "Sim, enquanto ele estiver pendente: use \"Cancelar\" no histórico da tela Férias. Depois de aprovado, fale com o seu gestor."}
        |push:{categoria: "ponto", titulo: "Esqueci de marcar o ponto. O que faço?", conteudo: "Em Ponto, na visão Mês, marque \"Ajuste\" no dia, escolha a célula e informe o horário. O pedido vai para o seu superior ou para o RH. O dia de hoje só pode ser corrigido a partir de amanhã."}
        |push:{categoria: "ponto", titulo: "O que significam (I) e (D) na planilha do mês?", conteudo: "(I) é uma marcação incluída por correção aprovada. (D) é uma marcação desconsiderada, que não conta nas horas. A marcação original nunca é apagada."}
        |push:{categoria: "ponto", titulo: "O que é o saldo do dia?", conteudo: "São as horas trabalhadas menos a jornada do seu contrato, em dia útil. Diferença de até 10 minutos no dia não conta (CLT, art. 58). Em folga, feriado, férias e ausência justificada, a jornada esperada é zero."}
        |push:{categoria: "ponto", titulo: "O que é o descanso entre jornadas?", conteudo: "São 11 horas entre o fim de um dia de trabalho e o começo do seguinte (CLT, art. 66). Se você for marcar antes disso, a tela avisa quanto falta."}
        |push:{categoria: "ponto", titulo: "Faltei com atestado. Como registro?", conteudo: "Em Ponto, na visão Hoje, use \"Registrar ausência ou atestado\" e entregue o atestado ao RH. Não escreva diagnóstico nem código CID no sistema."}
        |push:{categoria: "documentos", titulo: "Como envio um documento?", conteudo: "Na tela Documentos, escolha o documento pendente e informe o link do arquivo. O RH confere e você vê o resultado na mesma tela."}
        |push:{categoria: "documentos", titulo: "O que significa \"Atrasada\" numa pendência?", conteudo: "Que o prazo de envio passou e o documento ainda não chegou. Envie assim que puder."}
        |push:{categoria: "documentos", titulo: "Meu documento foi recusado. E agora?", conteudo: "O motivo aparece no documento, na tela Documentos. Corrija e envie de novo."}
        |push:{categoria: "politicas_internas", titulo: "Como mudo meu telefone ou endereço?", conteudo: "Em Perfil, no cartão \"Contato e endereço\". Nome, CPF, data de nascimento e cargo mudam por solicitação ao RH, no mesmo Perfil."}
        |push:{categoria: "politicas_internas", titulo: "Quem vê meus dados bancários?", conteudo: "Só o RH e o Admin, para o pagamento. Seu gestor não vê."}
        |push:{categoria: "politicas_internas", titulo: "Como peço uma cópia dos meus dados?", conteudo: "Em Configurações, na aba Privacidade, use \"Baixar meus dados\". Para corrigir ou apagar dados, faça o pedido ao RH ali mesmo; a resposta vem em até 15 dias (LGPD)."}
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

    // Sem Admin, assina o primeiro RH ativo (o RH tambem publica a FAQ).
    conditional {
      if ($autor_id == null) {
        var.update $autor_id {
          value = $autor_rh_id
        }
      }
    }

    precondition ($autor_id != null) {
      error_type = "standard"
      error = "Nao ha usuario ADMIN ou RH ativo para assinar os artigos."
    }

    db.query artigo_faq {
      return = {type: "list"}
    } as $existentes

    // Titulos ja cadastrados, como texto ("|titulo|"): o contains em lista nao reconhece o item.
    var $titulos {
      value = "|"
    }

    foreach ($existentes) {
      each as $e {
        var.update $titulos {
          value = $titulos ~ $e.titulo ~ "|"
        }
      }
    }

    var $criados {
      value = 0
    }

    foreach ($artigos) {
      each as $a {
        conditional {
          if (($titulos|contains:("|" ~ $a.titulo ~ "|")) == false) {
            db.add artigo_faq {
              data = {
                categoria            : $a.categoria
                titulo               : $a.titulo
                conteudo             : $a.conteudo
                publicado_por_user_id: $autor_id
                ativo                : true
                updated_at           : "now"
              }
            } as $novo

            var.update $criados {
              value = $criados + 1
            }
          }
        }
      }
    }
  }

  response = {
    criados    : $criados
    ja_existiam: ($artigos|count) - $criados
  }

  tags = ["conectahr"]
  guid = "conectahr-semear-faq-0001"
}
