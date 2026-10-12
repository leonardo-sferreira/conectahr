# Proposal

## Why

O ponto do ConectaRH foi feito como controle interno experimental: guarda um registro por dia com quatro horários fixos, a correção aprovada sobrescreve o horário e não há comprovante, NSR nem os arquivos que a fiscalização pede. Para valer como registro de ponto, ele precisa seguir a Portaria MTP nº 671/2021 no modelo de software (REP-P). Ao mesmo tempo, quem usa a tela pediu (12/10/2026) que os dias antes da admissão deixem de aparecer como falta, que o espelho mostre só o dia e o mês em formato de planilha, e que as férias sigam a CLT, com venda de dias e um calendário com os feriados.

## What Changes

**Ponto (REP-P, Portaria 671/2021, arts. 74 a 91 e Anexo IX):**
- Cada marcação passa a ser gravada num armazenamento só de inclusão (ARP), com NSR sequencial da empresa, CPF, data e hora com fuso, data e hora da gravação, coletor ("02", navegador) e hash SHA-256 encadeado com a marcação anterior. Nada é alterado nem apagado. **BREAKING:** o registro do dia deixa de ser a fonte da verdade e passa a ser montado a partir das marcações e dos tratamentos.
- A pessoa pode marcar quantas vezes precisar, sem restrição de horário nem de quantidade (art. 74, I). As marcações do dia viram pares de entrada e saída, em ordem.
- **BREAKING:** correção e ajuste deixam de sobrescrever o horário. Viram um **tratamento** ao lado da marcação original: inclusão de marcação ou desconsideração de uma marcação, sempre com motivo (art. 82, parágrafo único). O fluxo de pedido, decisão e prazo continua igual.
- **Comprovante de Registro de Ponto do Trabalhador** (arts. 79 e 80) em PDF depois de cada marcação, sem a pessoa pedir, e disponível para baixar por pelo menos 48 horas.
- **Espelho de ponto** com o conteúdo do art. 84: empregador, trabalhador com admissão e cargo, período, horário contratual, marcações originais e tratadas (incluída ou desconsiderada) e as horas de cada dia.
- **AFD** (leiaute oficial de 31/07/2026, registros 1, 2, 5, 6, 7 e 9) e **AEJ** (registros 01 a 08 e 99), gerados pelo RH para um intervalo de datas.
- Cadastro do **empregador** (CNPJ ou CPF, razão social, local da prestação de serviço) e dos dados do REP-P (número de registro no INPI, CNPJ do desenvolvedor). As alterações entram no AFD (registro 2).

**Tela de ponto:**
- Dias anteriores à admissão ficam em branco, sem situação. A marcação só é aceita a partir da data de admissão.
- **BREAKING (tela):** sai a visão semanal. Ficam "Hoje" (as marcações do dia, com o comprovante de cada uma) e "Mês" (todas as marcações do mês numa planilha, uma linha por dia).

**Férias (CLT, arts. 134, 135 e 143):**
- O pedido precisa ser feito com pelo menos 45 dias de antecedência do início.
- Até 3 períodos por período aquisitivo, cada um com pelo menos 5 dias e um deles com pelo menos 14.
- **Venda de férias (abono pecuniário):** até 10 dias, pedida junto com um período.
- **Saldo por período aquisitivo:** 30 dias, descontando os dias pedidos, aprovados e vendidos. O pedido não pode passar do saldo e não pode deixar um saldo impossível de usar (menos de 5 dias, ou sem espaço para o período de 14).

**Calendário:**
- Feriados nacionais, pontos facultativos federais, o feriado estadual de São Paulo (9 de julho) e os municipais da cidade de São Paulo, com o tipo "feriado" ou "ponto facultativo". Carga inicial de 2026 e 2027, e o RH mantém pela tela de estrutura da empresa.
- Na tela de férias, um calendário mensal marca feriados, pontos facultativos, as férias da pessoa e o período que ela está escolhendo.

**Fora do escopo (non-goals):**
- Registro do programa no INPI e Atestado Técnico (art. 89). O sistema guarda o número informado pelo RH; o registro é de quem desenvolve.
- Assinatura com certificado ICP-Brasil: o comprovante em PDF sai sem assinatura PAdES e o AFD e o AEJ sem o arquivo `.p7s` CAdES (arts. 80 e 88). O registro de assinatura do arquivo traz o texto literal do leiaute, e as telas dizem que a assinatura não é feita.
- Sincronismo com a Hora Legal Brasileira (Anexo IX, item 2): vale o relógio do servidor do Xano, sem verificação contra o Observatório Nacional.
- Marcação off-line e outros coletores (aplicativo mobile, desktop): todo registro é on-line, pelo navegador.
- Ajuste de relógio (registro 4) e eventos sensíveis de energia (registro 6 com código "02"): o servidor em nuvem não tem esses eventos. Indisponibilidade e disponibilidade (códigos 07 e 08) são registradas quando o RH as informa.
- Redução das férias por faltas (CLT, art. 130), férias coletivas e o prazo para pedir o abono (art. 143, § 1º).
- Hora noturna reduzida e adicional noturno no espelho.

## Capabilities

### New Capabilities
<!-- nenhuma: o projeto concentra o comportamento numa capacidade só -->

### Modified Capabilities
- `conectahr`: o ponto deixa de ser "experimental" e passa a seguir o REP-P (ARP com NSR e hash, comprovante, tratamento, espelho do art. 84, AFD e AEJ, cadastro do empregador). "Registro de ponto e correcao" troca a sobrescrita do horário pelo tratamento e aceita marcações sem limite a partir da admissão. "Espelho de ponto mensal" passa a ter "Hoje" e "Mês" em planilha e dias em branco antes da admissão. Entram as regras de férias da CLT (antecedência de 45 dias, fracionamento, abono e saldo) e o calendário de feriados nacionais, facultativos e de São Paulo.

## Impact

- **Backend (Xano):** tabelas novas `marcacao_ponto` (ARP), `tratamento_ponto`, `empregador` e `evento_rep`; campo `tipo` em `feriado`; campo `dias_abono` em `ferias`. Endpoints alterados: `ponto/marcar`, os de correção e ajuste (`ponto/{id}/solicitar_correcao`, `ponto/solicitar_correcao_dia`, `correcoes_ponto/{id}/aprovar`, `folha_ponto/ajustar`), `meu_ponto`, `folha_ponto/mes`, `ferias/solicitacoes`, `minha_situacao_ferias` e `calendario`. Endpoints novos: comprovantes recentes, dados do AFD e do AEJ, cadastro do empregador e do REP-P, eventos do REP e feriados. Os cadastros e as alterações de colaborador passam a gerar o registro 5 do AFD.
- **Migração:** as marcações já gravadas em `registro_ponto` são copiadas para a ARP com NSR na ordem da marcação. Os horários originais (antes das correções aprovadas) vêm da auditoria e de `correcao_ponto`; quando não houver como saber o original, a marcação é copiada como está, e isso fica registrado na migração.
- **Frontend (Streamlit):** `pagina_ponto.py`, `ponto_modelo.py`, `ponto_mensal_modelo.py`, `pagina_folha_ponto.py`, `folha_modelo.py`, `pagina_ferias.py`, `ferias_modelo.py`, a tela de estrutura da empresa (feriados) e uma tela nova do RH para o empregador, o REP-P, o AFD e o AEJ. Os testes em `tools/` acompanham.
- **Dependência nova:** `fpdf2` (só Python, sem binários) para gerar o comprovante em PDF.
- **Figma:** redesenho da tela de ponto (Hoje e Mês em planilha, comprovante), da tela de férias (venda, saldo, calendário), da tela do RH para o REP-P e os arquivos, e dos feriados na estrutura da empresa, nos modos claro e escuro.
- **LGPD:** o CPF passa a entrar no comprovante, no AFD e no AEJ, documentos que a lei exige. É preciso atualizar o registro de operações, a retenção (a ARP não é apagada pelo prazo legal) e o aviso de privacidade.
- **Ordem:** depende de `concluir-frontend-streamlit` ser arquivada antes, porque altera os requisitos que ela criou ou mudou ("Registro de ponto e correcao" e "Espelho de ponto mensal").
