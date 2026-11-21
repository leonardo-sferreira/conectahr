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
| Tratamento que só acrescenta informação: inclusão ou desconsideração, com motivo (art. 82) | Tabela `tratamento_ponto`. Pedido do colaborador em `ponto/correcao` e decisão em `correcoes_ponto/{id}/aprovar`; ajuste direto do responsável em `folha_ponto/tratar`. Os endpoints antigos, que sobrescreviam o horário, foram desativados |
| Comprovante de registro de ponto em PDF, por 48 horas, sem pedido (arts. 79 e 80) | `ponto/marcar` devolve os dados e a tela oferece o PDF na hora; `ponto/comprovantes` lista os dos últimos 7 dias; PDF em `frontend/comprovante_ponto.py` (`fpdf2`), sem assinatura |
| Espelho de ponto com o conteúdo do art. 84 | Ponto → Mês (`frontend/pagina_ponto.py`): cabeçalho, planilha e CSV. O horário contratual é a jornada da regra do contrato, porque o cadastro não guarda os horários de entrada e saída |
| AFD ("004") e AEJ ("002") nos leiautes de 31/07/2026 (arts. 81 e 83) | `rep/afd` e `rep/aej` (só RH e Admin, auditados) entregam os registros; `frontend/rep_modelo.py` monta os arquivos e confere o AFD; tela do RH "Ponto eletrônico (REP-P)" |

## O que fica fora

- **Registro no INPI** (art. 91) e **atestado técnico** (art. 89): são do desenvolvedor do programa. O
  RH informa o número na tela do REP-P; os exemplos usam números marcados como fictícios.
- **Assinatura ICP-Brasil** (arts. 80 e 88): o comprovante em PDF sai sem assinatura PAdES, e o AFD e o
  AEJ, sem o arquivo `.p7s` CAdES. A última linha dos arquivos traz o texto
  "ASSINATURA_DIGITAL_EM_ARQUIVO_P7S", como pede o leiaute.
- **Hora Legal Brasileira** (Anexo IX, item 2): vale o relógio do servidor do Xano, sem conferência com
  o Observatório Nacional.
- **Marcação off-line e outros coletores** (aplicativo mobile ou desktop).
- **Registro 04 do AEJ (horário contratual):** o cadastro não guarda os horários de entrada e saída, então o
  AEJ sai sem esse registro e sem o `codHorContratual` da primeira entrada do dia (registro 05).
- **Ajuste de relógio** (registro 4) e **retorno de energia** (registro 6, código 02): não existem num
  servidor em nuvem.

## Testes por HTTP (12/10/2026)

Com uma conta de colaborador de teste e uma de RH, contra o backend publicado (`tools/testar_rep_p_http.py` e a
conferência complementar com o RH):

- colaborador: 403 em `empregador` e `rep/eventos`; marcações gravadas com NSR crescente, hash e dados do comprovante;
  comprovantes com as marcações recentes; pedido com horário no futuro recusado e pedido de inclusão pendente; 12/12.
- RH: empregador visto e salvo sem gravar registro 2; aprovação virou tratamento, com a marcação original na ARP e o
  dia AJUSTADO; ajuste direto como 2º tratamento; motivo curto recusado; folha sem CPF nem hash; 9/9 (mais 2 do
  empregador na rodada anterior).
- A cadeia de hashes da ARP confere, com NSR de 1 a 15 sem lacuna.

Os testes acharam e corrigiram dois erros: `ponto/comprovantes` respondia 500 e `folha_ponto/mes` voltava vazia
(ver as armadilhas em `xano-workspace/AGENTS.md`). As marcações e os tratamentos de teste ficam na ARP da conta de
teste, porque nada é apagado.

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

## Jornada: virada do dia, descanso e saldo (design D12 a D14, 12/10/2026)

Estas três regras valem para o ponto e não mudam a ARP: as marcações continuam como foram gravadas.

- **Virada do dia (D12):** o dia é o dia civil de Brasília. Dia que ficou aberto vira `Incompleto` em três momentos:
  - na primeira marcação do dia seguinte;
  - na rotina diária;
  - na tela, que já mostra o dia passado aberto como incompleto.

  O sistema nunca grava a saída no lugar da pessoa, porque a marcação automática é proibida (art. 74). A saída que faltou vem por pedido de correção.
- **Descanso entre jornadas (D13):** da última marcação válida do dia anterior até a primeira do dia.
  - Abaixo do mínimo, a marcação é gravada mesmo assim, porque restringir a marcação é proibido (art. 74). O mínimo é `regra_contrato.descanso_minimo_minutos`; vazio vale 660 (CLT, art. 66).
  - `ponto/marcar` avisa o superior direto (ou o Gestor do departamento) e o RH (`notificacao_interna`, tipo `descanso_interjornada`).
  - A tela "Hoje" pede confirmação antes; desistir não grava nada.
- **Saldo do dia com tolerância (D14):** `registro_ponto.saldo_minutos` é o tempo trabalhado menos a jornada do contrato.
  - **Jornada esperada:** a do contrato em dia útil. É zero em fim de semana, feriado ou ponto facultativo do calendário, férias aprovadas e ausência aprovada ou registrada.
  - **Tolerância:** diferença de até 10 minutos no dia vira 0; acima disso, conta a diferença inteira (CLT, art. 58, § 1º; Súmula 366 do TST).
  - **Simplificação:** a tolerância é diária, e não por marcação, porque o cadastro não tem horário de entrada e saída.
  - **Contrato sem jornada (PJ):** sem saldo.
  - **Banco de horas:** o saldo não vai para ele.
  - **Conferência:** os 7 cenários da spec, pela CLI (`xano function run`):

    | Cenário | Saldo |
    |---|---|
    | 7h30 em jornada de 8h | -30 |
    | 6h20 em jornada de 6h | +20 |
    | 7h52 | 0 |
    | Sábado, 4h | +240 |
    | PJ | Vazio |
    | Dia útil sem marcação | -480 |
    | 8h11 | +11 |

## Decisões técnicas

Ver o `design.md` da change `ponto-rep-p-e-ferias-clt` (D1 a D11).
