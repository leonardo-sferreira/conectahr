// Resultados do termometro de humor (change termometro-de-humor, D4), so agregados. RH e Admin: todos os setores
// (ou um, com departamento_id); Gestor: so os setores em que e o gestor (outro setor e recusado). Devolve:
// - ciclos: os ultimos 9 (90 dias), com a quantidade de respostas e a distribuicao das 5 notas no escopo;
// - departamentos: cada setor no ciclo atual e no anterior, com a quantidade e a distribuicao;
// - motivos do ciclo atual e a participacao (respondentes e pessoas ativas no escopo).
// Grupo com menos respostas que o minimo (INDICADORES_MINIMO_PESSOAS, padrao 5) sai sem distribuicao. Se num ciclo so
// um setor ficar abaixo do minimo, o menor dos outros tambem sai sem, para a subtracao do total nao revelar o pequeno.
query "humor/resultados" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int? departamento_id?
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

    var $ano {
      value = ($hoje|substr:0:4)|to_int
    }

    var $mes {
      value = ($hoje|substr:5:2)|to_int
    }

    var $dia {
      value = ($hoje|substr:8:2)|to_int
    }

    var $a_jd {
      value = ((14 - $mes) / 12)|floor
    }

    var $y_jd {
      value = $ano + 4800 - $a_jd
    }

    var $m_jd {
      value = $mes + (12 * $a_jd) - 3
    }

    var $parte_mes {
      value = (((153 * $m_jd) + 2) / 5)|floor
    }

    var $bissextos {
      value = (($y_jd / 4)|floor) - (($y_jd / 100)|floor) + (($y_jd / 400)|floor)
    }

    var $dia_juliano {
      value = $dia + $parte_mes + (365 * $y_jd) + $bissextos - 32045
    }

    var $ciclo {
      value = (($dia_juliano - 2461335) / 10)|floor
    }

    var $minimo {
      value = ($env.INDICADORES_MINIMO_PESSOAS != null ? ($env.INDICADORES_MINIMO_PESSOAS|to_int) : 5)
    }

    var $e_rh {
      value = ($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")
    }

    precondition ($e_rh || ($perfil_autenticado == "GESTOR")) {
      error_type = "accessdenied"
      error = "Somente RH, Admin ou Gestor veem o termometro."
    }

    var $filtro {
      value = ($input.departamento_id == null) ? 0 : $input.departamento_id
    }

    var $deps_escopo {
      value = []
    }

    conditional {
      if ($e_rh) {
        db.query departamento {
          where = $db.departamento.ativo == true
          sort = {departamento.nome: "asc"}
          return = {type: "list"}
          output = ["id", "nome"]
        } as $deps_rh

        var.update $deps_escopo {
          value = $deps_rh
        }
      }

      else {
        db.get colaborador {
          field_name = "user_id"
          field_value = $usuario_autenticado.id
        } as $colaborador_gestor

        precondition ($colaborador_gestor != null) {
          error_type = "accessdenied"
          error = "Nao existe um colaborador vinculado a esta conta."
        }

        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_gestor.id && $db.departamento.ativo == true
          sort = {departamento.nome: "asc"}
          return = {type: "list"}
          output = ["id", "nome"]
        } as $deps_gestor

        precondition (($deps_gestor|count) > 0) {
          error_type = "accessdenied"
          error = "Voce nao e gestor de nenhum departamento."
        }

        var.update $deps_escopo {
          value = $deps_gestor
        }
      }
    }

    // Os setores que quem pede pode escolher no filtro (antes de aplicar o filtro).
    var $deps_permitidos {
      value = $deps_escopo
    }

    // Com filtro: so aquele setor, e ele precisa estar no escopo de quem pede.
    conditional {
      if ($filtro > 0) {
        var $so_filtro {
          value = []
        }

        foreach ($deps_escopo) {
          each as $d {
            conditional {
              if ($d.id == $filtro) {
                var.update $so_filtro {
                  value = $so_filtro|push:$d
                }
              }
            }
          }
        }

        precondition (($so_filtro|count) == 1) {
          error_type = "accessdenied"
          error = "Departamento fora do que voce pode ver."
        }

        var.update $deps_escopo {
          value = $so_filtro
        }
      }
    }

    // RH sem filtro: tambem quem nao tem departamento (0).
    conditional {
      if ($e_rh && ($filtro == 0)) {
        var.update $deps_escopo {
          value = $deps_escopo|push:{id: 0, nome: "Sem departamento"}
        }
      }
    }

    var $escopo_texto {
      value = ","
    }

    foreach ($deps_escopo) {
      each as $d {
        var.update $escopo_texto {
          value = $escopo_texto ~ ($d.id|to_text) ~ ","
        }
      }
    }

    var $primeiro_ciclo {
      value = $ciclo - 8
    }

    db.query humor_contagem {
      where = $db.humor_contagem.ciclo >= $primeiro_ciclo && $db.humor_contagem.ciclo <= $ciclo
      return = {type: "list"}
    } as $linhas

    // Mapas: "ciclo|nota" (escopo inteiro) e "ciclo|departamento|nota".
    var $por_ciclo {
      value = {}
    }

    var $por_dep {
      value = {}
    }

    foreach ($linhas) {
      each as $l {
        var $agulha_dep {
          value = "," ~ ($l.departamento_id|to_text) ~ ","
        }

        conditional {
          if ($escopo_texto|contains:$agulha_dep) {
            var $chave_c {
              value = ($l.ciclo|to_text) ~ "|" ~ ($l.nota|to_text)
            }

            var $atual_c {
              value = $por_ciclo|get:$chave_c
            }

            var $novo_c {
              value = (($atual_c == null) ? 0 : $atual_c) + $l.quantidade
            }

            var.update $por_ciclo {
              value = $por_ciclo|set:$chave_c:$novo_c
            }

            var $chave_d {
              value = ($l.ciclo|to_text) ~ "|" ~ ($l.departamento_id|to_text) ~ "|" ~ ($l.nota|to_text)
            }

            var $atual_d {
              value = $por_dep|get:$chave_d
            }

            var $novo_d {
              value = (($atual_d == null) ? 0 : $atual_d) + $l.quantidade
            }

            var.update $por_dep {
              value = $por_dep|set:$chave_d:$novo_d
            }
          }
        }
      }
    }

    var $deslocamentos {
      value = [8, 7, 6, 5, 4, 3, 2, 1, 0]
    }

    var $ciclos {
      value = []
    }

    var $respostas_atual {
      value = 0
    }

    foreach ($deslocamentos) {
      each as $desl {
        var $c {
          value = $ciclo - $desl
        }

        var $prefixo_c {
          value = $c|to_text
        }

        var $notas_c {
          value = []
        }

        var $notas_c_total {
          value = 0
        }

        var $chave_notas_c_1 {
          value = $prefixo_c ~ "|1"
        }

        var $bruto_notas_c_1 {
          value = $por_ciclo|get:$chave_notas_c_1
        }

        var $q_notas_c_1 {
          value = ($bruto_notas_c_1 == null) ? 0 : $bruto_notas_c_1
        }

        var.update $notas_c {
          value = $notas_c|push:$q_notas_c_1
        }

        var.update $notas_c_total {
          value = $notas_c_total + $q_notas_c_1
        }

        var $chave_notas_c_2 {
          value = $prefixo_c ~ "|2"
        }

        var $bruto_notas_c_2 {
          value = $por_ciclo|get:$chave_notas_c_2
        }

        var $q_notas_c_2 {
          value = ($bruto_notas_c_2 == null) ? 0 : $bruto_notas_c_2
        }

        var.update $notas_c {
          value = $notas_c|push:$q_notas_c_2
        }

        var.update $notas_c_total {
          value = $notas_c_total + $q_notas_c_2
        }

        var $chave_notas_c_3 {
          value = $prefixo_c ~ "|3"
        }

        var $bruto_notas_c_3 {
          value = $por_ciclo|get:$chave_notas_c_3
        }

        var $q_notas_c_3 {
          value = ($bruto_notas_c_3 == null) ? 0 : $bruto_notas_c_3
        }

        var.update $notas_c {
          value = $notas_c|push:$q_notas_c_3
        }

        var.update $notas_c_total {
          value = $notas_c_total + $q_notas_c_3
        }

        var $chave_notas_c_4 {
          value = $prefixo_c ~ "|4"
        }

        var $bruto_notas_c_4 {
          value = $por_ciclo|get:$chave_notas_c_4
        }

        var $q_notas_c_4 {
          value = ($bruto_notas_c_4 == null) ? 0 : $bruto_notas_c_4
        }

        var.update $notas_c {
          value = $notas_c|push:$q_notas_c_4
        }

        var.update $notas_c_total {
          value = $notas_c_total + $q_notas_c_4
        }

        var $chave_notas_c_5 {
          value = $prefixo_c ~ "|5"
        }

        var $bruto_notas_c_5 {
          value = $por_ciclo|get:$chave_notas_c_5
        }

        var $q_notas_c_5 {
          value = ($bruto_notas_c_5 == null) ? 0 : $bruto_notas_c_5
        }

        var.update $notas_c {
          value = $notas_c|push:$q_notas_c_5
        }

        var.update $notas_c_total {
          value = $notas_c_total + $q_notas_c_5
        }

        // A expressao fica fora do push: o Xano recusa ternario dentro do argumento de um filtro.
        var $notas_c_visiveis {
          value = ($notas_c_total >= $minimo) ? $notas_c : null
        }

        var $item_ciclo {
          value = {ciclo: $c, respostas: $notas_c_total, notas: $notas_c_visiveis}
        }

        var.update $ciclos {
          value = $ciclos|push:$item_ciclo
        }

        conditional {
          if ($desl == 0) {
            var.update $respostas_atual {
              value = $notas_c_total
            }
          }
        }
      }
    }

    // Setores no ciclo atual e no anterior, com a supressao abaixo do minimo.
    var $ciclo_anterior {
      value = $ciclo - 1
    }

    var $deps_brutos {
      value = []
    }

    foreach ($deps_escopo) {
      each as $d {
        var $prefixo_a {
          value = ($ciclo|to_text) ~ "|" ~ ($d.id|to_text)
        }

        var $notas_a {
          value = []
        }

        var $notas_a_total {
          value = 0
        }

        var $chave_notas_a_1 {
          value = $prefixo_a ~ "|1"
        }

        var $bruto_notas_a_1 {
          value = $por_dep|get:$chave_notas_a_1
        }

        var $q_notas_a_1 {
          value = ($bruto_notas_a_1 == null) ? 0 : $bruto_notas_a_1
        }

        var.update $notas_a {
          value = $notas_a|push:$q_notas_a_1
        }

        var.update $notas_a_total {
          value = $notas_a_total + $q_notas_a_1
        }

        var $chave_notas_a_2 {
          value = $prefixo_a ~ "|2"
        }

        var $bruto_notas_a_2 {
          value = $por_dep|get:$chave_notas_a_2
        }

        var $q_notas_a_2 {
          value = ($bruto_notas_a_2 == null) ? 0 : $bruto_notas_a_2
        }

        var.update $notas_a {
          value = $notas_a|push:$q_notas_a_2
        }

        var.update $notas_a_total {
          value = $notas_a_total + $q_notas_a_2
        }

        var $chave_notas_a_3 {
          value = $prefixo_a ~ "|3"
        }

        var $bruto_notas_a_3 {
          value = $por_dep|get:$chave_notas_a_3
        }

        var $q_notas_a_3 {
          value = ($bruto_notas_a_3 == null) ? 0 : $bruto_notas_a_3
        }

        var.update $notas_a {
          value = $notas_a|push:$q_notas_a_3
        }

        var.update $notas_a_total {
          value = $notas_a_total + $q_notas_a_3
        }

        var $chave_notas_a_4 {
          value = $prefixo_a ~ "|4"
        }

        var $bruto_notas_a_4 {
          value = $por_dep|get:$chave_notas_a_4
        }

        var $q_notas_a_4 {
          value = ($bruto_notas_a_4 == null) ? 0 : $bruto_notas_a_4
        }

        var.update $notas_a {
          value = $notas_a|push:$q_notas_a_4
        }

        var.update $notas_a_total {
          value = $notas_a_total + $q_notas_a_4
        }

        var $chave_notas_a_5 {
          value = $prefixo_a ~ "|5"
        }

        var $bruto_notas_a_5 {
          value = $por_dep|get:$chave_notas_a_5
        }

        var $q_notas_a_5 {
          value = ($bruto_notas_a_5 == null) ? 0 : $bruto_notas_a_5
        }

        var.update $notas_a {
          value = $notas_a|push:$q_notas_a_5
        }

        var.update $notas_a_total {
          value = $notas_a_total + $q_notas_a_5
        }

        var $prefixo_p {
          value = ($ciclo_anterior|to_text) ~ "|" ~ ($d.id|to_text)
        }

        var $notas_p {
          value = []
        }

        var $notas_p_total {
          value = 0
        }

        var $chave_notas_p_1 {
          value = $prefixo_p ~ "|1"
        }

        var $bruto_notas_p_1 {
          value = $por_dep|get:$chave_notas_p_1
        }

        var $q_notas_p_1 {
          value = ($bruto_notas_p_1 == null) ? 0 : $bruto_notas_p_1
        }

        var.update $notas_p {
          value = $notas_p|push:$q_notas_p_1
        }

        var.update $notas_p_total {
          value = $notas_p_total + $q_notas_p_1
        }

        var $chave_notas_p_2 {
          value = $prefixo_p ~ "|2"
        }

        var $bruto_notas_p_2 {
          value = $por_dep|get:$chave_notas_p_2
        }

        var $q_notas_p_2 {
          value = ($bruto_notas_p_2 == null) ? 0 : $bruto_notas_p_2
        }

        var.update $notas_p {
          value = $notas_p|push:$q_notas_p_2
        }

        var.update $notas_p_total {
          value = $notas_p_total + $q_notas_p_2
        }

        var $chave_notas_p_3 {
          value = $prefixo_p ~ "|3"
        }

        var $bruto_notas_p_3 {
          value = $por_dep|get:$chave_notas_p_3
        }

        var $q_notas_p_3 {
          value = ($bruto_notas_p_3 == null) ? 0 : $bruto_notas_p_3
        }

        var.update $notas_p {
          value = $notas_p|push:$q_notas_p_3
        }

        var.update $notas_p_total {
          value = $notas_p_total + $q_notas_p_3
        }

        var $chave_notas_p_4 {
          value = $prefixo_p ~ "|4"
        }

        var $bruto_notas_p_4 {
          value = $por_dep|get:$chave_notas_p_4
        }

        var $q_notas_p_4 {
          value = ($bruto_notas_p_4 == null) ? 0 : $bruto_notas_p_4
        }

        var.update $notas_p {
          value = $notas_p|push:$q_notas_p_4
        }

        var.update $notas_p_total {
          value = $notas_p_total + $q_notas_p_4
        }

        var $chave_notas_p_5 {
          value = $prefixo_p ~ "|5"
        }

        var $bruto_notas_p_5 {
          value = $por_dep|get:$chave_notas_p_5
        }

        var $q_notas_p_5 {
          value = ($bruto_notas_p_5 == null) ? 0 : $bruto_notas_p_5
        }

        var.update $notas_p {
          value = $notas_p|push:$q_notas_p_5
        }

        var.update $notas_p_total {
          value = $notas_p_total + $q_notas_p_5
        }

        var.update $deps_brutos {
          value = $deps_brutos|push:{id: $d.id, nome: $d.nome, a_total: $notas_a_total, a_notas: $notas_a, p_total: $notas_p_total, p_notas: $notas_p}
        }
      }
    }

    // Supressao por subtracao: so um setor pequeno (com alguma resposta) no ciclo -> o menor visivel tambem sai.
    var $pequenos_a {
      value = 0
    }

    var $pequenos_p {
      value = 0
    }

    var $menor_a_id {
      value = -1
    }

    var $menor_a_total {
      value = 999999
    }

    var $menor_p_id {
      value = -1
    }

    var $menor_p_total {
      value = 999999
    }

    foreach ($deps_brutos) {
      each as $b {
        conditional {
          if (($b.a_total > 0) && ($b.a_total < $minimo)) {
            var.update $pequenos_a {
              value = $pequenos_a + 1
            }
          }

          elseif (($b.a_total >= $minimo) && ($b.a_total < $menor_a_total)) {
            var.update $menor_a_total {
              value = $b.a_total
            }

            var.update $menor_a_id {
              value = $b.id
            }
          }
        }

        conditional {
          if (($b.p_total > 0) && ($b.p_total < $minimo)) {
            var.update $pequenos_p {
              value = $pequenos_p + 1
            }
          }

          elseif (($b.p_total >= $minimo) && ($b.p_total < $menor_p_total)) {
            var.update $menor_p_total {
              value = $b.p_total
            }

            var.update $menor_p_id {
              value = $b.id
            }
          }
        }
      }
    }

    var $departamentos {
      value = []
    }

    foreach ($deps_brutos) {
      each as $b {
        var $mostra_a {
          value = ($b.a_total >= $minimo) && (($pequenos_a != 1) || ($b.id != $menor_a_id))
        }

        var $mostra_p {
          value = ($b.p_total >= $minimo) && (($pequenos_p != 1) || ($b.id != $menor_p_id))
        }

        var $notas_a_visiveis {
          value = $mostra_a ? $b.a_notas : null
        }

        var $notas_p_visiveis {
          value = $mostra_p ? $b.p_notas : null
        }

        var $item_dep {
          value = {id: $b.id, nome: $b.nome, atual: {respostas: $b.a_total, notas: $notas_a_visiveis}, anterior: {respostas: $b.p_total, notas: $notas_p_visiveis}}
        }

        var.update $departamentos {
          value = $departamentos|push:$item_dep
        }
      }
    }

    // Motivos do ciclo atual, so com o minimo de respostas no escopo.
    var $motivos {
      value = null
    }

    conditional {
      if ($respostas_atual >= $minimo) {
        db.query humor_motivo_contagem {
          where = $db.humor_motivo_contagem.ciclo == $ciclo
          return = {type: "list"}
        } as $linhas_motivo

        var.update $motivos {
          value = {}
        }

        foreach ($linhas_motivo) {
          each as $lm {
            var $agulha_m {
              value = "," ~ ($lm.departamento_id|to_text) ~ ","
            }

            conditional {
              if ($escopo_texto|contains:$agulha_m) {
                var $chave_m {
                  value = $lm.motivo
                }

                var $atual_m {
                  value = $motivos|get:$chave_m
                }

                var $novo_m {
                  value = (($atual_m == null) ? 0 : $atual_m) + $lm.quantidade
                }

                var.update $motivos {
                  value = $motivos|set:$chave_m:$novo_m
                }
              }
            }
          }
        }
      }
    }

    // Participacao: pessoas ativas no escopo (respondentes = respostas do ciclo atual).
    db.query colaborador {
      where = $db.colaborador.status != "Desligado"
      return = {type: "list"}
      output = ["departamento_id"]
    } as $ativos_todos

    var $ativos {
      value = 0
    }

    foreach ($ativos_todos) {
      each as $p {
        var $dep_p {
          value = ($p.departamento_id == null) ? 0 : $p.departamento_id
        }

        var $agulha_p {
          value = "," ~ ($dep_p|to_text) ~ ","
        }

        conditional {
          if ($escopo_texto|contains:$agulha_p) {
            var.update $ativos {
              value = $ativos + 1
            }
          }
        }
      }
    }
  }

  response = {
    sucesso      : true
    hoje         : $hoje
    ciclo        : $ciclo
    minimo       : $minimo
    ciclos       : $ciclos
    departamentos: $departamentos
    motivos      : $motivos
    participacao : {respondentes: $respostas_atual, ativos: $ativos}
    pode_filtrar : $deps_permitidos
  }

  guid = "conectahr-humor-resultados-get-0001"
}
