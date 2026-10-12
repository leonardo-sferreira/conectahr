// Registros da ARP do REP-P num intervalo de datas, em ordem de NSR (change
// ponto-rep-p-e-ferias-clt): marcacoes (tipo 7) pelo dia da marcacao; empregador, empregado e
// eventos (tipos 2, 5 e 6) pelo dia da gravacao. Base do AFD (rep/afd) e da conferencia da cadeia
// de hashes. So leitura.
function "ConectaHR/registros_arp" {
  input {
    text inicio
    text fim
  }

  stack {
    // Do inicio do dia inicial (Brasilia) ate o fim do dia final.
    var $inicio_ms {
      value = ($input.inicio|to_timestamp) + 10800000
    }

    var $fim_ms {
      value = ($input.fim|to_timestamp) + 10800000 + 86400000
    }

    db.query marcacao_ponto {
      where = ($db.marcacao_ponto.tipo_registro == 7 && $db.marcacao_ponto.data >= $input.inicio && $db.marcacao_ponto.data <= $input.fim) || ($db.marcacao_ponto.tipo_registro != 7 && $db.marcacao_ponto.data_hora_gravacao >= $inicio_ms && $db.marcacao_ponto.data_hora_gravacao < $fim_ms)
      sort = {marcacao_ponto.nsr: "asc"}
      return = {type: "list"}
      output = ["id", "nsr", "tipo_registro", "colaborador_id", "cpf", "data", "data_hora_marcacao_txt", "data_hora_gravacao_txt", "coletor", "offline", "hash", "hash_anterior", "cpf_responsavel", "dados"]
    } as $registros
  }

  response = $registros

  tags = ["conectahr"]
  guid = "conectahr-registros-arp-0001"
}
