// Campos de cada tipo de documento (change campos-por-tipo-de-documento, D1 a D4). Confere os obrigatorios do tipo,
// as opcoes fechadas, a UF, as datas e o formato da CNH, e devolve a primeira falha em `erro` (ou null), as colunas
// comuns so quando o tipo as usa e `dados` so com as chaves do tipo. O CPF (tipo CPF, CIN e responsavel legal) e
// conferido pelo endpoint com ConectaHR/validar_cpf: funcao nao chama funcao neste workspace.
// Minimizacao (D2): laudo e ASO nao tem CID nem diagnostico.
function "ConectaHR/validar_campos_documento" {
  input {
    text tipo
    text? numero_documento?
    text? estado_de_emissao?
    date? data_emissao?
    date? data_validade?
    json? dados?
  }

  stack {
    var $t {
      value = "," ~ $input.tipo ~ ","
    }

    var $d {
      value = ($input.dados != null ? $input.dados : {})
    }

    // ---------- Valores informados, aparados ----------
    var $numero {
      value = ($input.numero_documento != null ? ($input.numero_documento|trim) : "")
    }

    var $uf {
      value = ($input.estado_de_emissao != null ? ($input.estado_de_emissao|trim|to_upper) : "")
    }

    var $emissao {
      value = ($input.data_emissao != null ? ($input.data_emissao|to_timestamp|format_timestamp:"Y-m-d":"UTC") : "")
    }

    var $validade {
      value = ($input.data_validade != null ? ($input.data_validade|to_timestamp|format_timestamp:"Y-m-d":"UTC") : "")
    }

    var $orgao {
      value = (($d|get:"orgao_emissor") != null ? (($d|get:"orgao_emissor")|to_text|trim|to_upper) : "")
    }

    var $categoria {
      value = (($d|get:"categoria") != null ? (($d|get:"categoria")|to_text|trim|to_upper) : "")
    }

    var $serie {
      value = (($d|get:"serie") != null ? (($d|get:"serie")|to_text|trim) : "")
    }

    var $resultado {
      value = (($d|get:"resultado") != null ? (($d|get:"resultado")|to_text|trim|to_lower) : "")
    }

    var $crm {
      value = (($d|get:"crm") != null ? (($d|get:"crm")|to_text|trim|to_upper) : "")
    }

    var $curso {
      value = (($d|get:"curso") != null ? (($d|get:"curso")|to_text|trim) : "")
    }

    var $instituicao {
      value = (($d|get:"instituicao") != null ? (($d|get:"instituicao")|to_text|trim) : "")
    }

    var $nivel {
      value = (($d|get:"nivel") != null ? (($d|get:"nivel")|to_text|trim|to_lower) : "")
    }

    var $conselho {
      value = (($d|get:"conselho") != null ? (($d|get:"conselho")|to_text|trim|to_upper) : "")
    }

    var $responsavel_nome {
      value = (($d|get:"responsavel_nome") != null ? (($d|get:"responsavel_nome")|to_text|trim) : "")
    }

    var $responsavel_cpf {
      value = (($d|get:"responsavel_cpf") != null ? (($d|get:"responsavel_cpf")|to_text|trim) : "")
    }

    var $vinculo {
      value = (($d|get:"vinculo") != null ? (($d|get:"vinculo")|to_text|trim|to_lower) : "")
    }

    var $descricao {
      value = (($d|get:"descricao") != null ? (($d|get:"descricao")|to_text|trim) : "")
    }

    // Campos dos tipos da change documentos-obrigatorios-por-contrato.
    var $zona {
      value = (($d|get:"zona") != null ? (($d|get:"zona")|to_text|trim) : "")
    }

    var $secao {
      value = (($d|get:"secao") != null ? (($d|get:"secao")|to_text|trim) : "")
    }

    var $tipo_certidao {
      value = (($d|get:"tipo_certidao") != null ? (($d|get:"tipo_certidao")|to_text|trim|to_lower) : "")
    }

    var $apolice {
      value = (($d|get:"apolice_seguro") != null ? (($d|get:"apolice_seguro")|to_text|trim) : "")
    }

    var $razao_social {
      value = (($d|get:"razao_social") != null ? (($d|get:"razao_social")|to_text|trim) : "")
    }

    var $natureza {
      value = (($d|get:"natureza") != null ? (($d|get:"natureza")|to_text|trim|to_lower) : "")
    }

    // ---------- Quais campos cada tipo usa (D1) ----------
    var $usa_numero {
      value = (",rg,cpf,cin,cnh,ctps,registro_profissional,documentacao_migratoria,certificado_reservista,titulo_eleitor,certidao_civil,cartao_cnpj,outro,"|contains:$t)
    }

    var $exige_numero {
      value = ($usa_numero && $input.tipo != "outro" && $input.tipo != "certidao_civil")
    }

    var $usa_uf {
      value = (",rg,cin,cnh,ctps,registro_profissional,titulo_eleitor,"|contains:$t)
    }

    var $exige_uf {
      value = ($usa_uf && $input.tipo != "ctps")
    }

    var $usa_emissao {
      value = (",rg,cin,cnh,aso_admissional,laudo_deficiencia,certificado_profissional,comprovante_residencia,comprovante_escolaridade,documentacao_migratoria,certificado_reservista,certidao_civil,termo_compromisso_estagio,cartao_cnpj,contrato_social,outro,"|contains:$t)
    }

    var $exige_emissao {
      value = ($usa_emissao && $input.tipo != "outro" && $input.tipo != "certidao_civil" && $input.tipo != "cartao_cnpj")
    }

    var $usa_validade {
      value = (",cin,cnh,certificado_profissional,registro_profissional,documentacao_migratoria,termo_compromisso_estagio,outro,"|contains:$t)
    }

    var $exige_validade {
      value = ($input.tipo == "cin" || $input.tipo == "cnh" || $input.tipo == "termo_compromisso_estagio")
    }

    // ---------- Rotulos das mensagens ----------
    var $rotulo_numero {
      value = ($input.tipo == "rg" ? "o numero do RG" : ($input.tipo == "cpf" ? "o numero do CPF" : ($input.tipo == "cin" ? "o numero da CIN (o CPF)" : ($input.tipo == "cnh" ? "o numero de registro da CNH" : ($input.tipo == "ctps" ? "o numero da CTPS" : ($input.tipo == "documentacao_migratoria" ? "o numero do RNM" : ($input.tipo == "certificado_reservista" ? "o numero do certificado" : ($input.tipo == "titulo_eleitor" ? "o numero do titulo" : ($input.tipo == "cartao_cnpj" ? "o CNPJ" : "o numero do registro")))))))))
    }

    var $rotulo_emissao {
      value = (($input.tipo == "rg" || $input.tipo == "cin") ? "a data de expedicao" : ($input.tipo == "aso_admissional" ? "a data do exame" : ($input.tipo == "laudo_deficiencia" ? "a data do laudo" : ($input.tipo == "certificado_profissional" ? "a data de conclusao" : ($input.tipo == "comprovante_escolaridade" ? "a data de conclusao ou da declaracao" : ($input.tipo == "termo_compromisso_estagio" ? "o inicio do estagio" : ($input.tipo == "contrato_social" ? "a data do registro ou da ultima alteracao" : "a data de emissao")))))))
    }

    // ---------- Obrigatorios, na ordem da tela ----------
    var $faltas {
      value = []
    }

    conditional {
      if ($input.tipo == "outro" && $descricao == "") {
        var.update $faltas {
          value = $faltas|push:"Informe que documento e."
        }
      }
    }

    conditional {
      if ($input.tipo == "documentacao_responsavel_legal") {
        conditional {
          if ($responsavel_nome == "") {
            var.update $faltas {
              value = $faltas|push:"Informe o nome do responsavel."
            }
          }
        }

        conditional {
          if ($responsavel_cpf == "") {
            var.update $faltas {
              value = $faltas|push:"Informe o CPF do responsavel."
            }
          }
        }

        conditional {
          if ($vinculo == "") {
            var.update $faltas {
              value = $faltas|push:"Informe o vinculo com o responsavel."
            }
          }
        }
      }
    }

    conditional {
      if ($input.tipo == "registro_profissional" && $conselho == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o conselho."
        }
      }
    }

    conditional {
      if ($input.tipo == "comprovante_escolaridade" && $nivel == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o nivel de escolaridade."
        }
      }
    }

    conditional {
      if ($input.tipo == "certificado_profissional" && $curso == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o curso ou a certificacao."
        }
      }
    }

    conditional {
      if (($input.tipo == "certificado_profissional" || $input.tipo == "comprovante_escolaridade") && $instituicao == "") {
        var.update $faltas {
          value = $faltas|push:"Informe a instituicao."
        }
      }
    }

    conditional {
      if ($input.tipo == "certidao_civil" && $tipo_certidao == "") {
        var.update $faltas {
          value = $faltas|push:"Informe se e certidao de nascimento ou de casamento."
        }
      }
    }

    conditional {
      if ($input.tipo == "termo_compromisso_estagio" && $instituicao == "") {
        var.update $faltas {
          value = $faltas|push:"Informe a instituicao de ensino."
        }
      }
    }

    conditional {
      if ($input.tipo == "termo_compromisso_estagio" && $apolice == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o numero da apolice do seguro contra acidentes."
        }
      }
    }

    conditional {
      if ($input.tipo == "cartao_cnpj" && $razao_social == "") {
        var.update $faltas {
          value = $faltas|push:"Informe a razao social."
        }
      }
    }

    conditional {
      if ($input.tipo == "contrato_social" && $natureza == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o tipo da empresa."
        }
      }
    }

    conditional {
      if ($exige_numero && $numero == "") {
        var.update $faltas {
          value = $faltas|push:("Informe " ~ $rotulo_numero ~ ".")
        }
      }
    }

    conditional {
      if (($input.tipo == "rg" || $input.tipo == "cin") && $orgao == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o orgao emissor."
        }
      }
    }

    conditional {
      if ($input.tipo == "cnh" && $categoria == "") {
        var.update $faltas {
          value = $faltas|push:"Informe a categoria da CNH."
        }
      }
    }

    conditional {
      if ($exige_uf && $uf == "") {
        var.update $faltas {
          value = $faltas|push:"Informe a UF."
        }
      }
    }

    conditional {
      if ($input.tipo == "titulo_eleitor" && ($zona == "" || $secao == "")) {
        var.update $faltas {
          value = $faltas|push:"Informe a zona e a secao eleitoral."
        }
      }
    }

    conditional {
      if ($input.tipo == "aso_admissional" && $resultado == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o resultado do exame."
        }
      }
    }

    conditional {
      if (($input.tipo == "aso_admissional" || $input.tipo == "laudo_deficiencia") && $crm == "") {
        var.update $faltas {
          value = $faltas|push:"Informe o CRM do medico."
        }
      }
    }

    conditional {
      if ($exige_emissao && $emissao == "") {
        var.update $faltas {
          value = $faltas|push:("Informe " ~ $rotulo_emissao ~ ".")
        }
      }
    }

    conditional {
      if ($exige_validade && $validade == "") {
        var.update $faltas {
          value = $faltas|push:"Informe a validade."
        }
      }
    }

    // ---------- Formatos e opcoes fechadas ----------
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $limite_residencia {
      value = now|add_secs_to_timestamp:-7776000|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    conditional {
      if ($uf != "" && $usa_uf && (",AC,AL,AP,AM,BA,CE,DF,ES,GO,MA,MT,MS,MG,PA,PB,PR,PE,PI,RJ,RN,RS,RO,RR,SC,SP,SE,TO,"|contains:("," ~ $uf ~ ",")) == false) {
        var.update $faltas {
          value = $faltas|push:"UF invalida. Use a sigla do estado, como SP."
        }
      }
    }

    conditional {
      if ($categoria != "" && $input.tipo == "cnh" && (",A,B,AB,C,D,E,AC,AD,AE,ACC,"|contains:("," ~ $categoria ~ ",")) == false) {
        var.update $faltas {
          value = $faltas|push:"Categoria da CNH invalida."
        }
      }
    }

    conditional {
      if ($resultado != "" && $input.tipo == "aso_admissional" && $resultado != "apto" && $resultado != "inapto") {
        var.update $faltas {
          value = $faltas|push:"O resultado do exame deve ser Apto ou Inapto."
        }
      }
    }

    conditional {
      if ($nivel != "" && $input.tipo == "comprovante_escolaridade" && (",fundamental,medio,tecnico,superior,pos_graduacao,mestrado,doutorado,"|contains:("," ~ $nivel ~ ",")) == false) {
        var.update $faltas {
          value = $faltas|push:"Nivel de escolaridade invalido."
        }
      }
    }

    conditional {
      if ($vinculo != "" && $input.tipo == "documentacao_responsavel_legal" && (",pai,mae,tutor,curador,outro,"|contains:("," ~ $vinculo ~ ",")) == false) {
        var.update $faltas {
          value = $faltas|push:"Vinculo com o responsavel invalido."
        }
      }
    }

    // CNH: numero de registro com 11 digitos (pontos, tracos e espacos sao ignorados).
    var $numero_cnh {
      value = $numero|replace:".":""|replace:"-":""|replace:" ":""
    }

    var $sobra_cnh {
      value = $numero_cnh|replace:"0":""|replace:"1":""|replace:"2":""|replace:"3":""|replace:"4":""|replace:"5":""|replace:"6":""|replace:"7":""|replace:"8":""|replace:"9":""
    }

    conditional {
      if ($input.tipo == "cnh" && $numero != "" && (($numero_cnh|strlen) != 11 || $sobra_cnh != "")) {
        var.update $faltas {
          value = $faltas|push:"O numero de registro da CNH tem 11 digitos."
        }
      }
    }

    var $numero_digitos {
      value = $numero|replace:".":""|replace:"-":""|replace:"/":""|replace:" ":""
    }

    var $sobra_numero {
      value = $numero_digitos|replace:"0":""|replace:"1":""|replace:"2":""|replace:"3":""|replace:"4":""|replace:"5":""|replace:"6":""|replace:"7":""|replace:"8":""|replace:"9":""
    }

    conditional {
      if ($input.tipo == "titulo_eleitor" && $numero != "" && (($numero_digitos|strlen) != 12 || $sobra_numero != "")) {
        var.update $faltas {
          value = $faltas|push:"O numero do titulo de eleitor tem 12 digitos."
        }
      }
    }

    conditional {
      if ($input.tipo == "cartao_cnpj" && $numero != "" && (($numero_digitos|strlen) != 14 || $sobra_numero != "")) {
        var.update $faltas {
          value = $faltas|push:"O CNPJ tem 14 digitos."
        }
      }
    }

    conditional {
      if ($tipo_certidao != "" && $input.tipo == "certidao_civil" && $tipo_certidao != "nascimento" && $tipo_certidao != "casamento") {
        var.update $faltas {
          value = $faltas|push:"Tipo de certidao invalido."
        }
      }
    }

    conditional {
      if ($natureza != "" && $input.tipo == "contrato_social" && (",mei,ltda,slu,sa,outra,"|contains:("," ~ $natureza ~ ",")) == false) {
        var.update $faltas {
          value = $faltas|push:"Tipo de empresa invalido."
        }
      }
    }

    conditional {
      if ($usa_emissao && $input.tipo != "termo_compromisso_estagio" && $emissao != "" && $emissao > $hoje) {
        var.update $faltas {
          value = $faltas|push:"A data de emissao nao pode ser futura."
        }
      }
    }

    conditional {
      if ($input.tipo == "comprovante_residencia" && $emissao != "" && $emissao < $limite_residencia) {
        var.update $faltas {
          value = $faltas|push:"Envie um comprovante de residencia dos ultimos 90 dias."
        }
      }
    }

    conditional {
      if ($usa_validade && $emissao != "" && $validade != "" && $validade < $emissao) {
        var.update $faltas {
          value = $faltas|push:"A data de validade nao pode ser anterior a data de emissao."
        }
      }
    }

    // ---------- Dados do tipo (so as chaves que ele usa, ate 100 caracteres) ----------
    var $dados_final {
      value = {}
    }

    conditional {
      if ($input.tipo == "rg" || $input.tipo == "cin") {
        var.update $dados_final {
          value = $dados_final|set:"orgao_emissor":($orgao|substr:0:100)
        }
      }
    }

    conditional {
      if ($input.tipo == "cnh") {
        var.update $dados_final {
          value = $dados_final|set:"categoria":$categoria
        }
      }
    }

    conditional {
      if ($input.tipo == "ctps" && $serie != "") {
        var.update $dados_final {
          value = $dados_final|set:"serie":($serie|substr:0:100)
        }
      }
    }

    conditional {
      if ($input.tipo == "aso_admissional") {
        var.update $dados_final {
          value = $dados_final|set:"resultado":$resultado
        }
      }
    }

    conditional {
      if ($input.tipo == "aso_admissional" || $input.tipo == "laudo_deficiencia") {
        var.update $dados_final {
          value = $dados_final|set:"crm":($crm|substr:0:100)
        }
      }
    }

    conditional {
      if (($input.tipo == "certificado_profissional" || $input.tipo == "comprovante_escolaridade") && $curso != "") {
        var.update $dados_final {
          value = $dados_final|set:"curso":($curso|substr:0:100)
        }
      }
    }

    conditional {
      if ($input.tipo == "certificado_profissional" || $input.tipo == "comprovante_escolaridade") {
        var.update $dados_final {
          value = $dados_final|set:"instituicao":($instituicao|substr:0:100)
        }
      }
    }

    conditional {
      if ($input.tipo == "comprovante_escolaridade") {
        var.update $dados_final {
          value = $dados_final|set:"nivel":$nivel
        }
      }
    }

    conditional {
      if ($input.tipo == "registro_profissional") {
        var.update $dados_final {
          value = $dados_final|set:"conselho":($conselho|substr:0:100)
        }
      }
    }

    conditional {
      if ($input.tipo == "documentacao_responsavel_legal") {
        var.update $dados_final {
          value = $dados_final|set:"responsavel_nome":($responsavel_nome|substr:0:100)|set:"responsavel_cpf":($responsavel_cpf|substr:0:14)|set:"vinculo":$vinculo
        }
      }
    }

    conditional {
      if ($input.tipo == "titulo_eleitor") {
        var.update $dados_final {
          value = $dados_final|set:"zona":($zona|substr:0:10)|set:"secao":($secao|substr:0:10)
        }
      }
    }

    conditional {
      if ($input.tipo == "certidao_civil") {
        var.update $dados_final {
          value = $dados_final|set:"tipo_certidao":$tipo_certidao
        }
      }
    }

    conditional {
      if ($input.tipo == "termo_compromisso_estagio") {
        var.update $dados_final {
          value = $dados_final|set:"instituicao":($instituicao|substr:0:100)|set:"apolice_seguro":($apolice|substr:0:100)
        }
      }
    }

    conditional {
      if ($input.tipo == "cartao_cnpj") {
        var.update $dados_final {
          value = $dados_final|set:"razao_social":($razao_social|substr:0:100)
        }
      }
    }

    conditional {
      if ($input.tipo == "contrato_social") {
        var.update $dados_final {
          value = $dados_final|set:"natureza":$natureza
        }
      }
    }

    conditional {
      if ($input.tipo == "outro") {
        var.update $dados_final {
          value = $dados_final|set:"descricao":($descricao|substr:0:100)
        }
      }
    }

    // CPF a conferir pelo endpoint (D3): o numero no tipo CPF e na CIN, o do responsavel no responsavel legal.
    var $cpf_a_conferir {
      value = (($input.tipo == "cpf" || $input.tipo == "cin") && $numero != "" ? $numero : ($input.tipo == "documentacao_responsavel_legal" && $responsavel_cpf != "" ? $responsavel_cpf : null))
    }
  }

  response = {
    erro             : (($faltas|count) > 0 ? ($faltas|first) : null)
    numero_documento : ($usa_numero && $numero != "" ? $numero : null)
    estado_de_emissao: ($usa_uf && $uf != "" ? $uf : "")
    data_emissao     : ($usa_emissao && $emissao != "" ? $emissao : null)
    data_validade    : ($usa_validade && $validade != "" ? $validade : null)
    dados            : $dados_final
    cpf_a_conferir   : $cpf_a_conferir
    cpf_da_ficha     : ($input.tipo == "cpf" || $input.tipo == "cin")
  }

  tags = ["conectahr"]
  guid = "conectahr-validar-campos-documento-0001"
}
