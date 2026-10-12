## MODIFIED Requirements

### Requirement: Registro de ponto e correcao
O sistema SHALL permitir que o colaborador marque o ponto quantas vezes precisar no dia, sem restrição de horário nem de quantidade, a partir da data de admissão; antes da admissão a marcação SHALL ser recusada. As marcações do dia SHALL ser lidas em ordem como pares de entrada e saída, e o sistema SHALL calcular as horas trabalhadas e extras quando aplicável. O dia SHALL usar os status ABERTO (número ímpar de marcações no dia corrente), COMPLETO, INCOMPLETO (número ímpar de marcações em dia anterior, depois da primeira marcação do dia seguinte ou da rotina diária) ou AJUSTADO (dia fechado, com número par de marcações, que tem algum tratamento). O número ímpar de marcações vale mais que o tratamento: um dia anterior com tratamento e uma marcação sem par SHALL ficar INCOMPLETO, para a saída que falta não sumir da vista. O colaborador SHALL poder solicitar a correção de um dia passado, com ou sem marcação, desde que o dia não seja anterior à admissão; o dia de hoje, ainda em andamento, não SHALL receber correção nem ajuste, que valem a partir do dia seguinte: pedir a inclusão de uma marcação que faltou ou a desconsideração de uma marcação indevida, com motivo. O horário pedido SHALL estar dentro do dia e não SHALL estar no futuro; uma marcação com pedido pendente não SHALL receber outro pedido. O responsável autorizado pela hierarquia (RH, Admin, o superior direto do colaborador ou, sem superior, o Gestor do departamento ou o substituto de uma delegação vigente desse Gestor) SHALL poder aprovar ou recusar com justificativa, nunca sobre o próprio registro. O mesmo responsável SHALL poder incluir ou desconsiderar diretamente uma marcação da sua equipe, com motivo; o ajuste segue as mesmas regras de horário, recalcula as horas, fica no histórico como correção aprovada, é auditado e avisa a pessoa. Nenhuma correção ou ajuste SHALL alterar ou apagar a marcação original: o resultado é um tratamento registrado ao lado dela.

#### Scenario: Jornada concluida
- **WHEN** o colaborador faz as marcações de entrada e saída do dia, em número par
- **THEN** o sistema calcula a jornada pelos pares e marca o dia como COMPLETO

#### Scenario: Marcacao antes da admissao
- **WHEN** alguém tenta marcar o ponto numa data anterior à sua admissão
- **THEN** o sistema recusa a marcação com mensagem clara e não grava nada

#### Scenario: Marcacoes sem limite
- **WHEN** o colaborador marca o ponto pela quinta vez no mesmo dia
- **THEN** o sistema grava a marcação, emite o comprovante e passa a ler três pares de entrada e saída

#### Scenario: Ajuste que deixa o dia sem par
- **WHEN** um dia anterior tem duas marcações incluídas por tratamento e uma original sem par
- **THEN** o dia fica INCOMPLETO, a planilha mostra as incluídas com "(I)" e a correção da saída que falta continua disponível

#### Scenario: Correcao aprovada
- **WHEN** o responsável com permissão aprova o pedido de inclusão de uma marcação de outro colaborador
- **THEN** o sistema registra o tratamento de inclusão com o motivo, mantém as marcações originais como estão, recalcula as horas e marca o dia como AJUSTADO

#### Scenario: Desconsideracao aprovada
- **WHEN** o responsável aprova o pedido de desconsiderar uma marcação feita por engano
- **THEN** a marcação continua gravada, passa a aparecer como desconsiderada no espelho e deixa de contar nas horas

#### Scenario: Jornada nao finalizada
- **WHEN** RH aciona a rotina diária e existe dia anterior com número ímpar de marcações
- **THEN** o sistema marca o dia como INCOMPLETO sem inventar marcações ausentes

#### Scenario: Correcao de dia sem marcacao
- **WHEN** o colaborador pede a inclusão de marcações num dia passado, posterior à admissão, em que não marcou nada
- **THEN** o sistema registra o pedido pendente para esse dia

#### Scenario: Horario invalido
- **WHEN** o horário pedido está fora do dia ou no futuro
- **THEN** o sistema recusa o pedido com mensagem clara, sem gravar nada

#### Scenario: Decisao fora da hierarquia
- **WHEN** alguém que não é RH, Admin, o superior direto nem, sem superior, o Gestor do departamento tenta decidir ou ajustar o ponto de outro colaborador
- **THEN** o sistema nega a operação

#### Scenario: Ajuste direto
- **WHEN** o responsável autorizado inclui ou desconsidera uma marcação de outra pessoa da sua equipe, com motivo
- **THEN** o sistema registra o tratamento, recalcula as horas, registra a correção como aprovada, audita a ação e notifica a pessoa

#### Scenario: Ajuste do proprio ponto
- **WHEN** alguém tenta ajustar diretamente o próprio ponto
- **THEN** o sistema nega o ajuste; o pedido segue para quem decide pela hierarquia

### Requirement: Espelho de ponto mensal
O sistema SHALL oferecer ao colaborador duas visões do próprio ponto: "Hoje", com as marcações do dia em ordem e o comprovante de cada uma, e "Mês", com todos os dias do mês numa planilha, uma linha por dia. Não SHALL haver visão semanal. O mês SHALL poder ser escolhido entre o mês da admissão e o mês atual. A planilha SHALL mostrar, por dia, a data completa (dd/mm/aaaa) e o dia da semana, todas as marcações em ordem (as incluídas por tratamento identificadas como incluídas e as desconsideradas identificadas como desconsideradas), as horas trabalhadas, o saldo do dia, o descanso entre jornadas quando for menor que o mínimo e uma situação, nesta ordem de precedência: dia anterior à admissão, em branco e sem nenhuma informação; dia com marcação ou tratamento; hoje sem marcação; férias aprovadas; ausência aprovada (pelo tipo: Atestado, Falta justificada, Licença ou Afastamento) ou em análise; ausência recusada, como Falta injustificada; feriado ou ponto facultativo; folga no fim de semana; dia útil sem nada, como "Sem registro" no mês corrente e "Falta injustificada" em mês encerrado. Dias futuros SHALL aparecer em branco. O espelho SHALL trazer o cabeçalho do art. 84 da Portaria nº 671/2021 (empregador, trabalhador com admissão e cargo, data de emissão, período e horário contratual), o resumo do mês (horas, horas positivas e horas negativas, dias com marcação, sem registro e faltas injustificadas), os pedidos de correção em análise e o motivo de uma correção recusada, e SHALL permitir baixar o mês em CSV.

#### Scenario: Consulta de um mes encerrado
- **WHEN** o colaborador escolhe um mês anterior
- **THEN** o sistema mostra cada dia do mês numa linha com todas as marcações e a situação, e o dia útil sem marcação nem ausência aparece como Falta injustificada

#### Scenario: Mes da admissao
- **WHEN** o colaborador admitido em 15/10 consulta outubro
- **THEN** os dias de 1 a 14 aparecem em branco, sem situação, e só a partir do dia 15 os dias úteis sem marcação contam como sem registro ou falta

#### Scenario: Visao do dia
- **WHEN** o colaborador abre "Hoje"
- **THEN** o sistema mostra as marcações do dia em ordem, com hora, NSR e o link do comprovante de cada uma

#### Scenario: Atestado aprovado
- **WHEN** um dia está coberto por um atestado aprovado
- **THEN** o espelho mostra o dia como Atestado, sem ação de correção

#### Scenario: Marcacao tratada no espelho
- **WHEN** um dia tem uma marcação desconsiderada e outra incluída por tratamento
- **THEN** a planilha mostra as duas, identificadas como desconsiderada e incluída, e as horas contam só a incluída

#### Scenario: Saldo e descanso no espelho
- **WHEN** o colaborador CLT abre um mês em que trabalhou 7h30 num dia útil e voltou depois de 9h de descanso em outro
- **THEN** a planilha mostra o saldo -0h30 no primeiro dia e "Descanso de 9h00 (mínimo 11h)" no segundo, e o resumo traz a soma dos saldos do mês

#### Scenario: Pedido de correcao a partir do espelho
- **WHEN** o colaborador escolhe corrigir um dia passado, com ou sem registro, dentro do prazo
- **THEN** o sistema abre o pedido só com as marcações que ainda não estão em análise

## REMOVED Requirements

### Requirement: Ponto experimental e conformidade futura
**Reason**: O ponto passa a seguir o REP-P da Portaria nº 671/2021, descrito em "Marcação de ponto no REP-P" e nos requisitos seguintes. O que este requisito garantia (marcação original imutável, ajuste separado, espelho para o trabalhador e registro de quem pediu e decidiu) continua valendo dentro deles.
**Migration**: As marcações de `registro_ponto` são copiadas para o armazenamento de marcações (ARP) com NSR na ordem em que foram feitas; as correções já aprovadas viram tratamentos.

## ADDED Requirements

### Requirement: Marcação de ponto no REP-P
O sistema SHALL funcionar como registrador eletrônico de ponto via programa (REP-P), conforme a Portaria MTP nº 671/2021 e o seu Anexo IX. Cada marcação SHALL ser gravada num armazenamento de registro de ponto (ARP) com: NSR (número sequencial de registro da empresa, começando em 1 e crescendo de um em um, sem repetir nem pular, compartilhado com os demais registros do AFD), CPF do trabalhador, data e hora da marcação com fuso horário, data e hora da gravação com fuso horário, identificador do coletor ("02", navegador), indicação de marcação on-line e código hash SHA-256 calculado sobre esses campos e o hash da marcação anterior. Os registros da ARP não SHALL ser alterados nem apagados por nenhum endpoint, perfil ou rotina, inclusive as de retenção e anonimização. O sistema não SHALL marcar ponto automaticamente nem com horário predefinido, não SHALL exigir autorização prévia para hora extra e não SHALL oferecer ao trabalhador nenhuma forma de alterar o que foi registrado (art. 74). A tela de marcação SHALL mostrar um relógio digital com horas, minutos e segundos.

#### Scenario: Marcacao gravada na ARP
- **WHEN** o colaborador marca o ponto
- **THEN** o sistema grava o registro com o próximo NSR, a hora do servidor com o fuso, o coletor "02" e o hash encadeado com a marcação anterior

#### Scenario: Cadeia de hash conferida
- **WHEN** o RH gera o AFD de um período
- **THEN** cada registro de marcação tem o hash igual ao SHA-256 dos seus campos com o hash do registro anterior, e qualquer alteração num registro quebra a conferência dos seguintes

#### Scenario: Tentativa de alterar a ARP
- **WHEN** qualquer usuário, inclusive Admin, tenta alterar ou apagar uma marcação gravada
- **THEN** não existe endpoint para isso e a marcação permanece como foi gravada

#### Scenario: NSR sem repeticao
- **WHEN** duas pessoas marcam o ponto ao mesmo tempo
- **THEN** cada marcação recebe um NSR diferente e a sequência continua sem lacuna

### Requirement: Comprovante de registro de ponto
Depois de cada marcação, o sistema SHALL disponibilizar ao trabalhador, sem que ele precise pedir, o "Comprovante de Registro de Ponto do Trabalhador" em PDF, com: o título; o NSR; a identificação do empregador (nome e CNPJ ou CPF, e CNO ou CAEPF quando houver); o local da prestação do serviço; o nome e o CPF do trabalhador; a data e o horário da marcação; o número de registro do programa no INPI; e o código hash SHA-256 da marcação (arts. 79 e 80). O trabalhador SHALL poder baixar os comprovantes das suas marcações das últimas 48 horas, no mínimo. O comprovante SHALL ser só do próprio trabalhador.

#### Scenario: Comprovante apos marcar
- **WHEN** o colaborador marca o ponto
- **THEN** a tela oferece na hora o PDF do comprovante dessa marcação, com todos os campos do art. 79

#### Scenario: Comprovantes recentes
- **WHEN** o colaborador abre o ponto no dia seguinte
- **THEN** a lista de comprovantes mostra as marcações das últimas 48 horas, cada uma com o seu PDF

#### Scenario: Comprovante de outra pessoa
- **WHEN** alguém pede o comprovante de uma marcação que não é sua
- **THEN** o sistema nega o acesso

### Requirement: Tratamento de marcações
O tratamento das marcações SHALL apenas acrescentar informação, sem alterar a ARP: incluir uma marcação que faltou ou desconsiderar uma marcação indevida, sempre com motivo, autor e data (art. 82, parágrafo único). O tratamento SHALL nascer só de um pedido de correção aprovado ou de um ajuste direto do responsável pela hierarquia. Desfazer um tratamento SHALL gerar outro tratamento, sem apagar o anterior.

#### Scenario: Inclusao com motivo
- **WHEN** o gestor inclui uma saída esquecida às 18h00 com o motivo "esqueceu de marcar"
- **THEN** o dia passa a ter a marcação incluída, identificada como tal no espelho e no AEJ, com o motivo, e a ARP continua sem essa marcação

#### Scenario: Tratamento sem motivo
- **WHEN** alguém tenta incluir ou desconsiderar uma marcação sem informar o motivo
- **THEN** o sistema recusa o tratamento

### Requirement: Cadastro do empregador e do REP-P
O RH e o Admin SHALL manter os dados do empregador usados no comprovante, no espelho, no AFD e no AEJ: tipo e número do identificador (CNPJ ou CPF), CNO ou CAEPF quando houver, razão social ou nome e local da prestação de serviço; e os dados do REP-P: número de registro do programa no INPI e o CNPJ ou CPF do desenvolvedor. Cada inclusão ou alteração dos dados do empregador SHALL gerar um registro na ARP (tipo 2 do AFD), com o CPF do responsável. A inclusão, a alteração e o desligamento de um colaborador SHALL gerar um registro de empregado na ARP (tipo 5 do AFD), com CPF e nome. O RH SHALL poder registrar a indisponibilidade e a volta da disponibilidade do serviço de ponto (tipo 6 do AFD, códigos 08 e 07). Toda alteração SHALL ser auditada. A marcação SHALL ser recusada enquanto o empregador não estiver cadastrado.

#### Scenario: Empregador alterado
- **WHEN** o RH altera a razão social
- **THEN** o sistema grava os novos dados, registra a alteração na ARP com o próximo NSR e o CPF de quem alterou, e audita a ação

#### Scenario: Empregador nao cadastrado
- **WHEN** alguém tenta marcar o ponto sem o empregador cadastrado
- **THEN** o sistema recusa a marcação e informa que o RH precisa cadastrar o empregador

#### Scenario: Colaborador incluido no REP
- **WHEN** o RH cadastra um colaborador
- **THEN** o sistema grava na ARP o registro de inclusão do empregado com CPF e nome

### Requirement: Arquivos AFD e AEJ
O RH e o Admin SHALL poder gerar, para um intervalo de datas: o Arquivo Fonte de Dados (AFD), com os registros da ARP do intervalo, no leiaute oficial publicado pelo Ministério do Trabalho e Emprego em 31/07/2026 (versão "004": cabeçalho tipo 1, registros 2, 5, 6 e 7, trailer tipo 9 e o registro de assinatura), em texto ISO 8859-1, uma linha por registro terminada em CR LF, ordenado por NSR, sem linhas em branco, com CRC-16/KERMIT nos registros 1 a 5, e nomeado "AFD" seguido do número do INPI, do CNPJ ou CPF do empregador e de "REP_P"; e o Arquivo Eletrônico de Jornada (AEJ), no leiaute oficial de 31/07/2026 (versão "002": registros 01 a 08 e 99 e o registro de assinatura), com os campos separados por "|", as marcações originais com a fonte "O", as incluídas com a fonte "I" e motivo, as desconsideradas com o tipo "D" e motivo, as faltas não justificadas e os movimentos do banco de horas. O registro de assinatura dos dois arquivos SHALL trazer o texto "ASSINATURA_DIGITAL_EM_ARQUIVO_P7S". A geração SHALL ser auditada e não SHALL estar disponível para Gestor nem Colaborador.

#### Scenario: AFD de um periodo
- **WHEN** o RH gera o AFD de 01/10/2026 a 31/10/2026
- **THEN** o sistema entrega o arquivo com o cabeçalho, os registros do período em ordem de NSR, o trailer com a contagem de cada tipo e o registro de assinatura, e cada linha confere com o tamanho e o CRC do leiaute

#### Scenario: AEJ com tratamento
- **WHEN** o RH gera o AEJ de um mês com uma marcação incluída e outra desconsiderada
- **THEN** o arquivo traz a incluída com a fonte "I" e o motivo, a desconsiderada com o tipo "D" e o motivo, e o trailer com a contagem de cada tipo

#### Scenario: Gestor tenta gerar o AFD
- **WHEN** um Gestor ou Colaborador pede o AFD ou o AEJ
- **THEN** o sistema nega o acesso

### Requirement: Férias pela CLT
Para colaborador cujo contrato permite férias, o pedido SHALL respeitar: início com pelo menos 45 dias de antecedência da data do pedido; cada período com pelo menos 5 dias corridos; até 3 períodos por período aquisitivo, um deles com pelo menos 14 dias; e o saldo do período aquisitivo, de 30 dias, menos os dias de férias e de abono já pedidos (pendentes ou aprovados). O pedido não SHALL deixar um saldo que não possa mais ser usado: depois dele, o saldo SHALL ser zero ou de pelo menos 5 dias, e, se nenhum período de 14 dias ou mais tiver sido pedido, o saldo restante SHALL comportar um. Junto com um período, o colaborador SHALL poder vender até 10 dias (abono pecuniário), uma vez por período aquisitivo; os dias vendidos saem do saldo. As férias não SHALL começar nos dois dias que antecedem um feriado ou o repouso semanal remunerado (CLT, art. 134, § 3º). O sistema SHALL mostrar à pessoa, antes de enviar, o saldo, os períodos já pedidos, os dias vendidos e o que ainda é possível pedir. As regras SHALL valer no backend; a tela só antecipa as mensagens.

#### Scenario: Pedido com menos de 45 dias
- **WHEN** o colaborador pede férias que começam daqui a 30 dias
- **THEN** o sistema recusa o pedido e informa que férias precisam ser pedidas com pelo menos 45 dias de antecedência

#### Scenario: Periodo curto demais
- **WHEN** o colaborador pede um período de 4 dias
- **THEN** o sistema recusa e informa que cada período precisa ter pelo menos 5 dias

#### Scenario: Venda de 10 dias e dois periodos
- **WHEN** o colaborador vende 10 dias e pede um primeiro período de 5 dias
- **THEN** o sistema aceita e informa que restam 15 dias, que precisam ser tirados num período só, de pelo menos 14 dias

#### Scenario: Saldo impossivel de usar
- **WHEN** o colaborador, com 30 dias de saldo, pede 27 dias
- **THEN** o sistema recusa, porque sobrariam 3 dias, menos do que um período permite

#### Scenario: Venda acima do limite
- **WHEN** o colaborador tenta vender 11 dias
- **THEN** o sistema recusa e informa que é possível vender no máximo 10 dias

#### Scenario: Inicio antes de feriado
- **WHEN** o colaborador escolhe começar as férias na véspera de um feriado
- **THEN** o sistema recusa e informa que as férias não podem começar nos dois dias antes de um feriado ou do descanso semanal

### Requirement: Calendário de feriados e pontos facultativos
O sistema SHALL manter os feriados com data, nome, abrangência (nacional, estadual ou municipal), tipo (feriado ou ponto facultativo) e, quando for o caso, estado e município. A carga inicial SHALL trazer, para 2026 e 2027: os feriados nacionais (incluindo a Sexta-feira Santa e o Dia Nacional de Zumbi e da Consciência Negra); os pontos facultativos federais (Carnaval, Quarta-feira de Cinzas, Corpus Christi e Dia do Servidor Público); o feriado do estado de São Paulo (Revolução Constitucionalista, 9 de julho); e os da cidade de São Paulo (aniversário da cidade, 25 de janeiro, e Corpus Christi, que no município é feriado). RH e Admin SHALL poder incluir, alterar e desativar feriados, com auditoria. O espelho de ponto SHALL tratar feriados como dia sem expediente e pontos facultativos conforme o tipo. A tela de férias SHALL mostrar um calendário mensal com os feriados, os pontos facultativos, as férias já pedidas e o período em escolha.

#### Scenario: Feriado no espelho
- **WHEN** o colaborador não marca ponto em 9 de julho
- **THEN** o espelho mostra o dia como feriado estadual de São Paulo, sem falta

#### Scenario: Calendario na escolha das ferias
- **WHEN** o colaborador escolhe o período das férias
- **THEN** o calendário mostra os feriados e pontos facultativos do mês, com o nome de cada um, e destaca o período escolhido

#### Scenario: RH inclui um feriado
- **WHEN** o RH inclui um feriado municipal
- **THEN** o sistema grava o feriado, audita a ação e passa a considerá-lo no espelho e no calendário

### Requirement: Jornada, descanso e saldo do dia
O dia de ponto SHALL ser o dia civil de Brasília. Uma jornada aberta (número ímpar de marcações) num dia que já passou SHALL ficar INCOMPLETO, sem nenhuma marcação gravada pelo sistema, e a primeira marcação do dia seguinte SHALL começar uma jornada nova. O sistema não SHALL recusar a marcação por causa do descanso entre jornadas (art. 74 da Portaria nº 671/2021); quando a pessoa for marcar antes de completar o descanso mínimo do contrato (11 horas pela CLT, art. 66) desde a última marcação do dia anterior com marcações, a tela SHALL avisar quanto falta e pedir confirmação; confirmada, a marcação SHALL ser gravada, o dia SHALL guardar o descanso real e o superior direto (ou, sem ele, o Gestor do departamento) e o RH SHALL ser avisados. O sistema SHALL calcular o saldo de cada dia como as horas trabalhadas menos a jornada diária do contrato da pessoa (`regra_contrato.horas_diarias`) nos dias úteis de segunda a sexta sem feriado, ponto facultativo, férias ou ausência justificada; nesses outros dias a jornada esperada é zero. Diferenças de até 10 minutos no dia não SHALL contar (CLT, art. 58, § 1º); acima disso, conta a diferença inteira. O dia útil de falta injustificada SHALL ter saldo igual a menos a jornada. Contrato sem jornada diária (PJ) não SHALL ter saldo. O saldo não SHALL ser lançado no banco de horas.

#### Scenario: Jornada aberta na virada do dia
- **WHEN** o colaborador marca a entrada às 08:00 e não marca a saída até o fim do dia
- **THEN** o dia fica INCOMPLETO sem saída inventada, e a primeira marcação do dia seguinte é a entrada desse dia

#### Scenario: Marcacao dentro do descanso confirmada
- **WHEN** o colaborador que marcou a última saída às 22:00 tenta marcar às 07:00 e confirma o aviso de que faltam 2h00 de descanso
- **THEN** o sistema grava a marcação, o dia mostra "Descanso de 9h00 (mínimo 11h)" e o superior e o RH recebem um aviso

#### Scenario: Marcacao dentro do descanso desistida
- **WHEN** o colaborador vê o aviso de descanso e desiste
- **THEN** nada é gravado

#### Scenario: Saida antes da jornada
- **WHEN** um colaborador CLT trabalha 7h30 num dia útil
- **THEN** o saldo do dia é -0h30

#### Scenario: Estagiario passa da jornada
- **WHEN** um estagiário com jornada de 6 horas trabalha 6h20 num dia útil
- **THEN** o saldo do dia é +0h20

#### Scenario: Diferenca dentro da tolerancia
- **WHEN** um colaborador CLT trabalha 7h52 num dia útil
- **THEN** o saldo do dia é 0h00

#### Scenario: Falta injustificada
- **WHEN** um dia útil de um mês encerrado fica sem marcação nem ausência
- **THEN** o saldo do dia é menos a jornada (-8h00 para CLT)

#### Scenario: Trabalho em folga ou feriado
- **WHEN** um colaborador CLT trabalha 4h00 num sábado ou feriado
- **THEN** o saldo do dia é +4h00

#### Scenario: Contrato sem jornada
- **WHEN** um colaborador PJ marca o ponto
- **THEN** o espelho não mostra saldo para ele

