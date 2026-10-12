# Design

## Context

- **Ponto hoje.** `registro_ponto` tem uma linha por pessoa e dia com quatro horários fixos (`hora_entrada`, `inicio_intervalo`, `fim_intervalo`, `hora_saida`), único por (`colaborador_id`, `data`). `ponto/marcar` preenche o próximo campo vazio. A correção aprovada (`correcoes_ponto/{id}/aprovar`) e o ajuste direto (`folha_ponto/ajustar`) **sobrescrevem** o horário; o valor anterior fica só em `correcao_ponto` e na auditoria. O frontend monta "Semana" e "Mês" a partir disso (`ponto_modelo.py`, `ponto_mensal_modelo.py`, `folha_modelo.py`).
- **Começo do mês.** `primeiro_dia()` usa a data mais antiga entre o primeiro registro e a admissão. Com a admissão antiga no cadastro, todos os dias desde então viram falta, e um registro anterior à admissão puxa o início para trás.
- **Férias hoje.** `ferias/solicitacoes` confere a matriz `regra_contrato` (antecedência, máximo de períodos, mínimo do período principal e dos outros), mas não tem saldo (tarefa 74 da `concluir-frontend-streamlit`), não tem abono e trata o **primeiro** período como o principal, quando a CLT exige que **algum** deles tenha 14 dias.
- **Feriados.** A tabela `feriado` tem `abrangencia` (nacional, estadual, municipal), sem distinguir feriado de ponto facultativo. O `calendario` GET existe; não há tela de calendário.
- **Fontes oficiais usadas:** Portaria MTP nº 671/2021, arts. 74 a 91 (texto em normaslegais.com.br); Anexo IX, na redação da Portaria MTP nº 1.486/2022; leiautes do AFD e do AEJ publicados no gov.br (MTE, Inspeção do Trabalho) em 31/07/2026. Os PDFs dos leiautes ficam citados em `docs/ponto/rep-p.md` (a criar), com o link e a data.
- **Restrições:** XanoScript sem tarefas agendadas e sem `regex_replace` confiável; Streamlit no frontend; o projeto é acadêmico e não tem registro no INPI nem certificado ICP-Brasil.

## Goals / Non-Goals

**Goals:**

- ARP só de inclusão, com NSR sem repetição e hash encadeado conferível de fora (por um script de teste).
- O registro do dia continua existindo, mas como **visão derivada** (marcações mais tratamentos), para não reescrever de uma vez tudo que lê `registro_ponto` (Central, folha, banco de horas, rotina diária).
- AFD e AEJ que batam campo a campo com o leiaute, conferidos por teste automatizado.
- Regras de férias da CLT no backend, com a tela só antecipando as mensagens.

**Non-Goals:**

- Assinatura PAdES/CAdES, registro no INPI, sincronismo com a Hora Legal Brasileira, coletor off-line (ver "Fora do escopo" na proposta).
- Mudar o banco de horas além de ler as horas pelos pares de marcações.

## Decisions

### D1. ARP numa tabela nova, `marcacao_ponto`, sem endpoint de edição

Campos: `nsr` (int, índice único), `tipo_registro` (2, 5, 6 ou 7), `colaborador_id`, `cpf`, `data_hora_marcacao` (timestamp), `fuso` ("-0300"), `data_hora_gravacao`, `coletor` ("02"), `offline` (false), `hash`, `hash_anterior`, e, para os tipos 2, 5 e 6, os campos do leiaute em `dados` (json) e `cpf_responsavel`. Nenhum endpoint faz `db.edit` ou `db.del` nela; `tools/checar_endpoints.py` passa a falhar se encontrar.

- *Alternativa:* acrescentar NSR e hash em `registro_ponto`. Rejeitada: a linha por dia com quatro campos não comporta marcações sem limite, e os campos são editados pela correção.
- *Alternativa:* tabelas separadas por tipo de registro. Rejeitada: o NSR é uma sequência só por estabelecimento para todos os tipos (Anexo IX, item 6, observação), e uma tabela única deixa o AFD numa consulta ordenada por NSR.

### D2. NSR pelo máximo + 1, protegido pelo índice único

`ConectaHR/gravar_registro_rep` busca o maior NSR e grava o seguinte. Se duas gravações colidirem, o índice único recusa uma e a chamada devolve erro; o frontend tenta a marcação de novo uma vez (o XanoScript do projeto não usa `try_catch`, e testá-lo deixaria funções de teste que não podem ser apagadas sem uma sincronização completa). Sem lacunas, porque nada é apagado.

- *Alternativa:* contador numa tabela `configuracao`. Rejeitada: ler e incrementar não é atômico no XanoScript; o índice único é a única garantia que o Xano dá.

### D3. Hash SHA-256 no backend, conferido em Python

O hash do registro 7 é o SHA-256 (hex minúsculo, 64 caracteres) da concatenação, sem separador, dos campos 1 a 7 **exatamente como saem no AFD** (NSR com 9 dígitos, "7", data e hora no formato DH com 24 caracteres, CPF com 12 dígitos, data e hora de gravação, "02", "0") seguida do hash do registro 7 anterior, quando existir. Gravar o hash já no formato do arquivo evita divergência entre o que foi calculado e o que é exportado. **Confirmado em 12/10/2026:** o filtro `sha256` do XanoScript devolve `ba7816bf…15ad` para "abc", e `ConectaHR/hash_registro_rep` dá o mesmo hash que o Python (`tools/testar_rep_p.py --xano`).

- O teste (`tools/testar_rep_p.py`) recalcula a cadeia inteira em Python com `hashlib` e confere registro por registro.

### D4. Tratamento em tabela própria; dia derivado

`tratamento_ponto`: `colaborador_id`, `data`, `tipo` (`inclusao` ou `desconsideracao`), `marcacao_id` (para desconsideração), `data_hora` (para inclusão), `motivo` (obrigatório), `autor_user_id`, `correcao_ponto_id` (quando vem de um pedido), `criado_em`. Não tem edição: desfazer cria outro tratamento.

- O dia é calculado por uma **função** do Xano (`ConectaHR/dia_de_ponto`) a partir das marcações e dos tratamentos: ordena, descarta as desconsideradas, soma as incluídas, forma os pares, calcula as horas e o status. A função alimenta `registro_ponto`, que vira um cache do dia, atualizado a cada marcação e a cada tratamento. Assim, a Central, a rotina diária e o banco de horas continuam lendo `registro_ponto` e a mudança fica contida.
- `correcao_ponto` passa a guardar `tipo` (`inclusao` ou `desconsideracao`), `marcacao_id` e `data_hora` pedida, no lugar de `campo` e `valor_solicitado`. Os pedidos antigos continuam legíveis.
- O cálculo puro fica em `ConectaHR/calcular_dia_ponto` (testável por `xano function run`, sem banco) e `ConectaHR/atualizar_dia_ponto` lê a ARP e os tratamentos e grava o cache. A ARP tem um campo `data` (dia local da marcação), fora do AFD, só para a consulta do dia.
- *Alternativa:* calcular o dia só no frontend. Rejeitada: o backend é dono das regras (AGENTS.md, seção 3), e o cálculo das horas precisa ser o mesmo para a pessoa, o gestor e o AEJ.

### D5. Comprovante e arquivos gerados em Python, a partir de dados do backend

O backend devolve os dados (`ponto/comprovantes` com as marcações das últimas 48 horas do próprio usuário; `rep/afd` e `rep/aej` com os registros do intervalo, só para RH e Admin, auditados). O frontend monta o PDF (`fpdf2`) e os arquivos de texto (`rep_modelo.py`: leiaute de posições fixas, CRC-16/KERMIT, encoding ISO 8859-1, CR LF).

- *Por quê:* o XanoScript não gera PDF e montar texto de posições fixas com CRC nele é frágil; em Python, o leiaute é testável com o exemplo do próprio leiaute ("123456789" → CRC "2189").
- *Risco aceito:* a regra de formatação fica no frontend. Ela não decide nada (os dados, o NSR e o hash vêm prontos do backend), então não fere o "frontend não é mecanismo de segurança".
- *Dependência nova:* `fpdf2` (licença LGPL, só Python). Alternativas: `reportlab` (maior, com partes em C) e HTML para PDF (exige um navegador ou o `wkhtmltopdf`, que o Streamlit Cloud não tem).

### D6. Empregador numa tabela de uma linha, `empregador`

Campos do registro 2 do AFD e do cabeçalho do AEJ, mais `inpi_registro`, `desenvolvedor_tipo_id`, `desenvolvedor_id`, `desenvolvedor_nome`, `desenvolvedor_email` e `ptrp_nome`/`ptrp_versao` (registro 08 do AEJ). `empregador` PUT grava e gera o registro 2 na ARP. Os registros 5 nascem em `colaboradores` POST, `colaboradores/{id}` PATCH (quando muda nome ou CPF) e na conclusão do desligamento (operação "E").

### D7. Admissão como início, nos dois lados

- Backend: `ponto/marcar` recusa quando a data local de hoje for anterior a `colaborador.data_admissao`; os pedidos de correção já recusam dia anterior à admissão.
- Frontend: `primeiro_dia()` passa a ser **só** a admissão (sem o mínimo com o primeiro registro). Sem admissão no cadastro, cai no primeiro registro, como hoje. Dias antes dela e dias futuros saem como linha em branco na planilha.
- A data de admissão errada no cadastro continua gerando falta; a correção é acertar o cadastro (informado ao usuário em 12/10/2026).

### D7b. A marcação nunca é recusada por horário

O `ponto/marcar` antigo recusava a volta do intervalo antes do mínimo e a saída com hora extra acima do limite sem autorização. O art. 74 da Portaria proíbe restringir a marcação e exigir autorização prévia para hora extra, então essas regras passam a só calcular e sinalizar (intervalo curto e extra acima do limite aparecem no espelho e na folha); a marcação sempre é gravada. Continuam recusadas: pessoa sem ficha, desligada, antes da admissão e empregador não cadastrado.

### D8. Planilha do mês com `st.dataframe`

Uma linha por dia: Data, Dia, os pares "Ent. 1", "Saí. 1", "Ent. 2"… (até o maior número de pares do mês, com as marcações originais e as incluídas), "Desconsideradas", Horas e Situação. As desconsideradas ficam numa coluna própria para não deslocar os pares. O `dataframe` não risca texto, então a incluída sai como "18:05 (I)" e a desconsiderada como "08:01 (D)", com a legenda abaixo. A correção do dia é pedida pela seleção da linha (`on_select`), não por botões em cada linha (Figma 464:826).

- *Alternativa:* tabela em HTML. Rejeitada: o pedido é "formato de planilha", e o `dataframe` dá rolagem, ordenação e cópia como numa planilha.

### D9. Saldo de férias calculado no backend, sem tabela nova

O período aquisitivo vigente começa na admissão e renova a cada `periodo_aquisitivo_meses` (12). O saldo é 30 menos os dias de férias e de abono dos pedidos `Pendente` e `Aprovada` cujo início cai no período concessivo daquele aquisitivo. `ferias` ganha `dias_abono` (0 a 10). `minha_situacao_ferias` devolve saldo, períodos pedidos, se já há período de 14 ou mais, dias vendidos e o mínimo do próximo período. A antecedência de 45 dias, o mínimo de 5, o de 14 e o limite de 10 ficam na matriz `regra_contrato` (CLT: `antecedencia_ferias`=45, `minimo_outros_periodos`=5, `minimo_periodo_principal`=14, `maximo_periodos`=3, novo `maximo_abono`=10), para que contratos diferentes possam ter outros valores.

- *Alternativa:* tabela `periodo_aquisitivo`. Adiada: sem férias coletivas nem redução por faltas, o cálculo pelas datas basta.

### D10. Feriados: campo `tipo` e carga por script

`feriado.tipo` (`feriado` ou `ponto_facultativo`). A carga de 2026 e 2027 é gerada por `tools/feriados.py`, que calcula a Páscoa (algoritmo de Meeus/Butcher) e as datas móveis (Carnaval = Páscoa − 47 e − 48, Cinzas = − 46, Sexta-feira Santa = − 2, Corpus Christi = + 60), e conferida contra a portaria de pontos facultativos do governo federal do ano. Na cidade de São Paulo, Corpus Christi é feriado municipal; no restante, ponto facultativo federal.

### D11. Figma primeiro

Antes de cada tela: seção 21 "Ponto REP-P" (Hoje, Mês em planilha, comprovante em PDF, estados), seção 22 "Férias pela CLT" (pedido com venda e saldo, calendário, mensagens), a tela do RH "Empregador, REP-P e arquivos" e a aba de feriados na estrutura da empresa, nos modos claro e escuro.

## Risks / Trade-offs

- [Migração com o original perdido: as correções antigas sobrescreveram horários] → Reconstruir o original a partir de `correcao_ponto.valor_anterior` e da auditoria; o que não tiver origem é migrado como está, e a migração grava um relatório com a contagem. Como é ambiente acadêmico, a base pode ser recriada se preferirem.
- [Corrida no NSR com muitas marcações simultâneas] → Índice único e até 3 tentativas; o volume do projeto é baixo.
- [Filtro SHA-256 inexistente no XanoScript] → Confirmar na primeira publicação (D3) antes de construir o resto.
- [Tempo de resposta de `ponto/marcar` com hash, NSR e recálculo do dia] → Uma consulta pelo último registro 7 (índice por NSR), e o recálculo só do dia da pessoa.
- [Leiaute muda de novo] → `rep_modelo.py` concentra o leiaute, com a versão ("004" e "002") num lugar só e os testes amarrados ao PDF citado.
- [Regras de férias barrando pedidos que o RH quer aceitar] → Os valores ficam na `regra_contrato` e as exceções individuais continuam valendo.
- [CPF em mais documentos (LGPD)] → O comprovante só para o dono; AFD e AEJ só para RH e Admin, auditados; atualizar `docs/lgpd/registro-de-operacoes.md` e `retencao.md` (a ARP fica fora da anonimização pelo prazo legal).

## Migration Plan

1. Publicar as tabelas novas e os campos novos (sem remover nada).
2. Cadastrar o empregador e o REP-P (tela do RH ou carga).
3. Rodar a migração (endpoint de uso único, só Admin, auditado): registros 5 para os colaboradores ativos, e as marcações de `registro_ponto` para a ARP na ordem de `data` e horário, com NSR e hash; correções aprovadas viram tratamentos.
4. Publicar os endpoints novos e os alterados; publicar o frontend.
5. **Volta atrás:** os endpoints antigos continuam no Git; a ARP e os tratamentos são só acréscimo, e `registro_ponto` continua preenchido, então voltar o frontend e os endpoints restaura o comportamento anterior sem perda.

### Migração executada (12/10/2026)

`ConectaHR/migrar_ponto_rep` (pela CLI, uma vez; recusa a segunda execução): 4 registros de empregado (tipo 5), 3 marcações (tipo 7) de 2 dias, nenhuma correção aprovada para converter em tratamento. A ARP ficou com NSR 1 (evento 07), 2 (empregador de exemplo), 3 a 6 (empregados) e 7 a 9 (marcações); a cadeia de hashes confere (`tools/testar_rep_p.py --xano`). A data e hora de gravação das marcações migradas é a da migração.

Duas armadilhas do XanoScript achadas aqui: numa lista literal (`[{v: $x.campo}]`) as variáveis não são avaliadas (usar `|push:`); e a variável do laço chegou nula dentro de um `else` com laço aninhado (copiar para uma variável de fora antes do condicional).

## Open Questions

- O número de registro no INPI e o CNPJ do desenvolvedor: o grupo informa os valores (ou usa os de exemplo marcados como fictícios) na tela do RH.

## Figma

- **Seção 21 "Ponto REP-P"** (463:822): Hoje 463:825, Mês em planilha 464:826, comprovante em PDF 465:830, pedido de correção para incluir 465:856 e para desconsiderar 465:894, estados 465:932; tela do RH "Ponto eletrônico (REP-P)" 467:834.
- **Seção 22 "Férias pela CLT"** (466:830): saldo, pedido e calendário 466:833; venda de dias, mensagens das regras e estados 466:1171.
- **Feriados:** aba da estrutura da empresa 468:838 (na seção 22).
- **Modo escuro:** seção 21 — Dark 468:1458 e seção 22 — Dark 468:2226, na página "Protótipo — Dark".
