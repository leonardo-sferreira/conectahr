# Ponto no modelo REP-P (Portaria MTP nº 671/2021)

Change `ponto-rep-p-e-ferias-clt`, desde 12/10/2026. Este documento substitui o "controle interno
experimental" descrito em [`../backlog-rep.md`](../backlog-rep.md).

## Situação, em uma frase

O ponto do ConectaRH segue os requisitos técnicos do registrador eletrônico de ponto via programa
(REP-P), mas **não vale como REP-P para a fiscalização**: falta o registro do programa no INPI, a
assinatura com certificado ICP-Brasil e o atestado técnico (arts. 88, 89 e 91). As telas não dizem
que o ponto é "certificado", "homologado" ou "em conformidade".

## Fontes oficiais usadas

| Fonte | Onde | Consultada em |
|---|---|---|
| Portaria MTP nº 671/2021, arts. 74 a 91 (registro eletrônico de ponto) | [texto em normaslegais.com.br](https://www.normaslegais.com.br/legislacao/portaria-mtp-671-2021.htm) | 12/10/2026 |
| Anexo IX, requisitos do REP-P (redação da Portaria MTP nº 1.486/2022) | [cópia em tdn.totvs.com.br](https://tdn.totvs.com.br/download/attachments/809504336/ANEXO-IX-REQUISITOS-DO-REGISTRADOR-ELETRONICO-DE-PONTO-VIA-PROGRAMA-REP-P.pdf?api=v2) | 12/10/2026 |
| Leiaute do Arquivo Fonte de Dados (AFD), versão "004" | [gov.br, MTE, 31/07/2026](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/fiscalizacao-do-trabalho/leiaute-do-arquivo-fonte-de-dados-afd.pdf) | 12/10/2026 |
| Leiaute do Arquivo Eletrônico de Jornada (AEJ), versão "002" | [gov.br, MTE, 31/07/2026](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/fiscalizacao-do-trabalho/leiaute-do-arquivo-eletronico-de-jornada-aej.pdf) | 12/10/2026 |
| Página do Registro Eletrônico de Ponto | [gov.br, MTE](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/fiscalizacao-do-trabalho/rep) | 12/10/2026 |

## O que é feito

| Requisito | Onde está no ConectaRH |
|---|---|
| Armazenamento de Registro de Ponto (ARP) só de inclusão, nada alterado nem apagado (Anexo IX, itens 6 e 7) | Tabela `marcacao_ponto`. `tools/checar_endpoints.py` falha se algum `.xs` editar, apagar ou truncar a tabela |
| NSR sequencial da empresa, começando em 1, para todos os registros (Anexo IX, item 6, obs.) | `ConectaHR/gravar_registro_rep`, com índice único em `nsr` |
| Registro da marcação com CPF, data e hora com fuso, gravação, coletor e hash SHA-256 (Anexo IX, item 10) | Registro tipo 7, coletor "02" (navegador), sempre on-line |
| Hash SHA-256 dos campos 1 a 7 do registro 7 mais o hash do registro 7 anterior (leiaute do AFD) | `ConectaHR/hash_registro_rep`; conferido em Python por `frontend/rep_modelo.py` |
| Empregador (tipo 2), empregado (tipo 5) e disponibilidade do serviço (tipo 6, códigos 07 e 08) na ARP | `empregador` PUT, `colaboradores` POST e PATCH, conclusão do desligamento, `rep/eventos` POST |
| Sem restrição de horário nem de quantidade de marcações, sem marcação automática, sem autorização prévia para hora extra e sem o trabalhador alterar o que foi registrado (art. 74) | `ponto/marcar` só recusa: sem ficha, desligado, antes da admissão e empregador não cadastrado |
| Tratamento que só acrescenta informação: inclusão ou desconsideração, com motivo (art. 82) | Tabela `tratamento_ponto` (a fazer nas tarefas 3.x) |
| Comprovante de registro de ponto em PDF, por 48 horas, sem pedido (arts. 79 e 80) | A fazer (tarefas 3.3 e 4.1) |
| Espelho de ponto com o conteúdo do art. 84 | A fazer (tarefa 4.4) |
| AFD e AEJ nos leiautes de 31/07/2026 (arts. 81 e 83) | A fazer (grupo 5) |

## O que fica fora

- **Registro no INPI** (art. 91) e **atestado técnico** (art. 89): são do desenvolvedor do programa. O
  RH informa o número na tela do REP-P; os exemplos usam números marcados como fictícios.
- **Assinatura ICP-Brasil** (arts. 80 e 88): o comprovante em PDF sai sem assinatura PAdES, e o AFD e o
  AEJ, sem o arquivo `.p7s` CAdES. A última linha dos arquivos traz o texto
  "ASSINATURA_DIGITAL_EM_ARQUIVO_P7S", como pede o leiaute.
- **Hora Legal Brasileira** (Anexo IX, item 2): vale o relógio do servidor do Xano, sem conferência com
  o Observatório Nacional.
- **Marcação off-line e outros coletores** (aplicativo mobile ou desktop).
- **Ajuste de relógio** (registro 4) e **retorno de energia** (registro 6, código 02): não existem num
  servidor em nuvem.

## Como conferir a cadeia de hashes

1. Gere o AFD do período (tela do RH, grupo 5) ou leia os registros tipo 7 de `marcacao_ponto` em ordem
   de NSR.
2. Para cada registro tipo 7, junte os campos 1 a 7 exatamente como no AFD (NSR com 9 dígitos, "7", a
   data e hora no formato `AAAA-MM-ddThh:mm:00-0300`, o CPF com 12 dígitos, a data e hora da gravação,
   o coletor e "0") e, no fim, o hash do registro 7 anterior (nada, no primeiro).
3. O SHA-256 em hexadecimal minúsculo dessa linha tem de ser igual ao hash gravado. Alterar qualquer
   campo de um registro quebra a conferência dele e de todos os seguintes.

`frontend/rep_modelo.py` (`conferir_cadeia`) faz isso, e `python tools/testar_rep_p.py --xano` compara o
cálculo do backend com o do Python.

## Decisões técnicas

Ver o `design.md` da change `ponto-rep-p-e-ferias-clt` (D1 a D11).
