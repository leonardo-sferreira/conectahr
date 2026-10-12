// Cadastra um empregador de exemplo, com dados ficticios, quando ainda nao ha nenhum
// (change ponto-rep-p-e-ferias-clt). Sem empregador o ponto nao e marcado; este cadastro
// libera o ambiente de desenvolvimento ate o RH informar os dados reais na tela do REP-P
// (empregador PUT). Grava o registro tipo 2 na ARP, sem responsavel (operacao do sistema).
// So roda pela CLI do Xano (funcoes nao sao expostas por HTTP). Se ja houver empregador,
// nao faz nada.
function "ConectaHR/empregador_inicial" {
  input {
  }

  stack {
    db.query empregador {
      sort = {empregador.id: "asc"}
      return = {type: "single"}
    } as $existente

    var $criado {
      value = null
    }

    conditional {
      if ($existente == null) {
        db.add empregador {
          data = {
            tipo_identificador              : "cnpj"
            identificador                   : "12345678000190"
            razao_social                    : "ConectaRH Tecnologia Ltda (ficticio)"
            local_prestacao                 : "Av. Paulista, 1000 - Bela Vista, Sao Paulo/SP"
            inpi_registro                   : "BR512026000000"
            desenvolvedor_tipo_identificador: "cnpj"
            desenvolvedor_identificador     : "12345678000190"
            desenvolvedor_nome              : "Grupo ConectaRH - Impacta (ficticio)"
            desenvolvedor_email             : "contato@conectarh.exemplo"
            ptrp_nome                       : "ConectaRH Ponto"
            ptrp_versao                     : "1.0"
            servico_disponivel              : true
            updated_at                      : "now"
          }
        } as $novo

        function.run "ConectaHR/gravar_registro_rep" {
          input = {tipo_registro: 2, cpf_responsavel: "", dados: {tipo_identificador: "1", identificador: "12345678000190", cno_caepf: "", razao_social: "ConectaRH Tecnologia Ltda (ficticio)", local_prestacao: "Av. Paulista, 1000 - Bela Vista, Sao Paulo/SP"}}
        } as $registro_rep

        var.update $criado {
          value = {empregador_id: $novo.id, nsr: $registro_rep.nsr}
        }
      }
    }
  }

  response = {ja_existia: ($existente != null), criado: $criado}

  tags = ["conectahr"]
  guid = "conectahr-empregador-inicial-0001"
}
