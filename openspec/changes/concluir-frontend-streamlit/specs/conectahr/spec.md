## MODIFIED Requirements

### Requirement: Autorizacao por perfil e estrutura organizacional
O sistema SHALL aplicar permissoes por perfil Admin, RH, Gestor ou Colaborador, restringindo dados conforme o escopo do usuario. O sistema SHALL permitir vincular cada colaborador a um gestor e cada gestor a uma unica area/departamento, impedindo acesso fora do escopo autorizado. O sistema SHALL permitir que RH ou Admin definam, na ficha de cada colaborador, um superior direto: outro colaborador que nao esteja desligado, nunca a propria pessoa e sem formar ciclo na cadeia. As decisoes sobre ponto, ferias e ausencias de um colaborador SHALL seguir esta hierarquia, qualquer que seja o perfil de quem decide: RH e Admin decidem todos; com superior direto definido, decide o superior; sem superior, decide o Gestor do departamento do colaborador; ninguem decide o proprio pedido.

#### Scenario: Colaborador consulta os proprios dados
- **WHEN** um Colaborador acessa um recurso pessoal
- **THEN** o sistema permite apenas seus proprios dados e operacoes explicitamente autorizadas

#### Scenario: Gestor consulta sua equipe
- **WHEN** um Gestor acessa colaboradores vinculados a sua area
- **THEN** o sistema retorna somente sua equipe e permite apenas decisoes previstas para o papel

#### Scenario: Acesso administrativo
- **WHEN** Admin ou RH acessa a gestao organizacional
- **THEN** o sistema permite as operacoes administrativas conforme suas permissoes e registra a acao

#### Scenario: Superior direto definido na ficha
- **WHEN** RH ou Admin define o superior direto de um colaborador com outra pessoa ativa que nao esta abaixo dele na cadeia
- **THEN** o sistema grava o superior, registra a acao na auditoria e passa a usar esse superior nas decisoes sobre a pessoa

#### Scenario: Superior que forma ciclo
- **WHEN** RH ou Admin tenta definir como superior a propria pessoa, alguem desligado ou alguem que ja esta abaixo dela na cadeia
- **THEN** o sistema recusa a alteracao com mensagem clara

#### Scenario: Superior sem o perfil Gestor
- **WHEN** um usuario com perfil Colaborador e superior direto de outra pessoa
- **THEN** o sistema permite que ele decida os pedidos dessa pessoa, como faria um Gestor, sem lhe dar acesso a outros dados de gestao

### Requirement: Registro de ponto e correcao
O sistema SHALL permitir registrar entrada, inicio e fim de intervalo e saida, acompanhar a jornada e calcular horas trabalhadas e extras quando aplicavel. O registro SHALL usar os status ABERTO, COMPLETO, INCOMPLETO ou AJUSTADO; um registro ABERTO de dia anterior SHALL passar a INCOMPLETO quando a rotina diaria for acionada. O colaborador SHALL poder solicitar correcao de uma marcacao de um dia com registro e tambem de um dia passado sem nenhuma marcacao, desde que o dia nao seja anterior a admissao. O horario pedido SHALL estar dentro do dia, nao SHALL estar no futuro e SHALL respeitar a ordem das marcacoes; uma marcacao com pedido pendente nao SHALL receber outro pedido. O responsavel autorizado pela hierarquia (RH, Admin, o superior direto do colaborador ou, sem superior, o Gestor do departamento ou o substituto de uma delegacao vigente desse Gestor) SHALL poder aprovar ou recusar com justificativa, nunca sobre o proprio registro. O mesmo responsavel SHALL poder ajustar diretamente uma marcacao da sua equipe, com justificativa: o ajuste segue as mesmas regras de horario, recalcula as horas, fica no historico como correcao aprovada, e auditado e avisa a pessoa.

#### Scenario: Jornada concluida
- **WHEN** o colaborador registra os marcadores necessarios do dia
- **THEN** o sistema calcula a jornada e marca o registro como COMPLETO

#### Scenario: Correcao aprovada
- **WHEN** o responsavel com permissao aprova uma solicitacao de correcao de outro colaborador
- **THEN** o sistema ajusta o registro, preserva o valor original, registra a decisao e marca o registro como AJUSTADO

#### Scenario: Jornada nao finalizada
- **WHEN** RH aciona a rotina diaria e existe registro ABERTO de um dia anterior
- **THEN** o sistema marca o registro como INCOMPLETO sem inventar marcacoes ausentes

#### Scenario: Correcao de dia sem marcacao
- **WHEN** o colaborador pede a correcao de um dia passado, posterior a admissao, em que nao ha registro
- **THEN** o sistema cria o registro do dia como INCOMPLETO e a solicitacao de correcao pendente

#### Scenario: Horario invalido
- **WHEN** o horario pedido esta fora do dia, no futuro ou fora da ordem das marcacoes
- **THEN** o sistema recusa o pedido com mensagem clara, sem alterar o registro

#### Scenario: Decisao fora da hierarquia
- **WHEN** alguem que nao e RH, Admin, o superior direto nem, sem superior, o Gestor do departamento tenta decidir ou ajustar o ponto de outro colaborador
- **THEN** o sistema nega a operacao

#### Scenario: Ajuste direto
- **WHEN** o responsavel autorizado ajusta uma marcacao de outra pessoa da sua equipe, com justificativa
- **THEN** o sistema grava o novo horario, recalcula as horas, registra a correcao como aprovada, audita a acao e notifica a pessoa

#### Scenario: Ajuste do proprio ponto
- **WHEN** alguem tenta ajustar diretamente o proprio ponto
- **THEN** o sistema nega o ajuste; o pedido segue para quem decide pela hierarquia

### Requirement: Ferias e ausencias
O sistema SHALL permitir solicitar ferias e registrar ausencias com acompanhamento de status. Ferias SHALL usar Pendente, Aprovada, Rejeitada, Cancelada ou Concluida. Ausencias SHALL usar Falta, Atestado, Afastamento, Licenca ou Outro e status Pendente, Aprovada, Rejeitada ou Registrado. As decisoes de ferias e a aprovacao ou recusa de ausencias SHALL seguir a hierarquia: RH e Admin decidem de qualquer colaborador; com superior direto definido, decide o superior; sem superior, decide o Gestor do departamento que o colaborador integra; o substituto de uma delegacao vigente do Gestor com escopo `ferias` ou `todas` SHALL decidir ferias dentro do mesmo escopo. A conferencia de conflitos de um pedido de ferias SHALL estar disponivel a quem pode decidi-lo. Registrar uma ausencia aprovada SHALL continuar restrito a RH e Admin. Ninguem SHALL decidir as proprias ferias nem as proprias ausencias. Toda decisao SHALL manter justificativa e responsavel. Nas ausencias, quem decide sem ser RH ou Admin SHALL consultar somente tipo, periodo e status, sem acesso ao atestado, documento anexado ou motivo.

#### Scenario: Ferias aprovadas
- **WHEN** RH, Admin, o superior direto, o Gestor do departamento de colaborador sem superior ou substituto com delegacao vigente aprova uma solicitacao pendente de outro colaborador
- **THEN** o sistema valida o periodo, registra a decisao e o responsavel e altera o status para Aprovada

#### Scenario: Gestor fora do escopo
- **WHEN** um Gestor tenta decidir ferias de colaborador de outro departamento, ou de colaborador que tem outro superior direto
- **THEN** o sistema nega a decisao

#### Scenario: Ausencia registrada
- **WHEN** uma ausencia e criada com tipo permitido e periodo valido
- **THEN** o sistema registra o evento e apresenta seu status conforme o fluxo aplicavel

#### Scenario: Gestor consulta ausencia da equipe
- **WHEN** um Gestor consulta as ausencias de um colaborador da sua equipe
- **THEN** o sistema retorna tipo, periodo e status, sem atestado, documento ou motivo clinico

#### Scenario: Superior decide ausencia
- **WHEN** o superior direto aprova ou recusa, com justificativa, a ausencia pendente de alguem da sua equipe
- **THEN** o sistema registra a decisao e o responsavel; depois de aprovada, a ausencia segue para o RH registrar

#### Scenario: Ausencia fora da hierarquia
- **WHEN** alguem que nao e RH, Admin, o superior direto nem, sem superior, o Gestor do departamento tenta decidir uma ausencia
- **THEN** o sistema nega a decisao

### Requirement: Central de tarefas e pendencias
O sistema SHALL apresentar uma central personalizada por perfil com documentos aguardando envio ou analise, ferias, ausencias e correcoes de ponto pendentes, avaliacoes nao respondidas, metas e PDIs atrasados, pendencia de senha temporaria, cadastro incompleto e jornadas do dia sem marcacao de saida. As filas de decisao SHALL seguir a hierarquia: quem e superior direto de alguem SHALL receber as filas da sua equipe, mesmo sem o perfil Gestor. A fila de ausencias SHALL trazer somente tipo, periodo e status, sem atestado nem motivo. A fila de documentos SHALL ficar com RH e Admin.

#### Scenario: Central do colaborador
- **WHEN** um colaborador que nao e superior de ninguem acessa sua central
- **THEN** o sistema exibe somente suas pendencias e as acoes autorizadas para resolve-las

#### Scenario: Central do gestor ou RH
- **WHEN** um gestor ou RH acessa sua central
- **THEN** o sistema exibe pendencias sob seu escopo e tarefas de aprovacao ou analise correspondentes

#### Scenario: Dashboard do gestor
- **WHEN** um Gestor acessa seu dashboard
- **THEN** o sistema exibe tamanho da equipe, ausencias, ferias proximas, avaliacoes pendentes e situacao do ponto do dia, restritos aos colaboradores da sua equipe

#### Scenario: Central do superior sem perfil Gestor
- **WHEN** um colaborador que e superior direto de outra pessoa acessa sua central
- **THEN** o sistema exibe as filas de ferias, ausencias e correcoes de ponto da sua equipe, alem das proprias pendencias, e indica que ele e superior

### Requirement: Base de conhecimento do RH
O sistema SHALL manter artigos de FAQ organizados por categoria (ferias, ponto, documentos, politicas internas), mantidos por RH ou Admin, e disponiveis para consulta por todos os colaboradores autenticados. A FAQ nao trata de beneficios; os beneficios de cada colaborador ficam no requisito "Beneficios do colaborador".

#### Scenario: Consulta de FAQ
- **WHEN** um colaborador busca ou navega pela base de conhecimento
- **THEN** o sistema exibe os artigos publicados, organizados por categoria

## ADDED Requirements

### Requirement: Espelho de ponto mensal
O sistema SHALL permitir que o colaborador consulte o próprio ponto mês a mês, de qualquer mês desde o primeiro ponto registrado ou a admissão, sem limite de meses. Cada dia, até hoje, SHALL aparecer uma única vez com as marcações, as horas trabalhadas e uma situação, nesta ordem de precedência: registro do dia; hoje sem marcação; férias aprovadas; ausência aprovada (pelo tipo: Atestado, Falta justificada, Licença ou Afastamento) ou em análise; ausência recusada, como Falta injustificada; feriado nacional; folga no fim de semana; dia útil sem nada, como "Sem registro" no mês corrente e "Falta injustificada" em mês encerrado. O espelho SHALL mostrar o resumo do mês (horas, dias com marcação, sem registro, faltas injustificadas e atestados), os pedidos de correção em análise e o motivo de uma correção recusada, e SHALL permitir baixar o mês em CSV.

#### Scenario: Consulta de um mês encerrado
- **WHEN** o colaborador escolhe um mês anterior
- **THEN** o sistema mostra cada dia do mês com a situação, e o dia útil sem marcação nem ausência aparece como Falta injustificada

#### Scenario: Atestado aprovado
- **WHEN** um dia está coberto por um atestado aprovado
- **THEN** o espelho mostra o dia como Atestado, sem ação de correção

#### Scenario: Pedido de correção a partir do espelho
- **WHEN** o colaborador escolhe corrigir um dia passado, com ou sem registro, dentro do prazo
- **THEN** o sistema abre o pedido só com as marcações que ainda não estão em análise

### Requirement: Folha de ponto da equipe e do RH
O sistema SHALL oferecer a consulta mensal do ponto das pessoas que o usuário pode ver: RH e Admin veem todos; os demais veem a si mesmos, quem os tem como superior direto e, entre quem não tem superior, as pessoas do departamento que gerenciam. A consulta SHALL trazer, por pessoa, horas, dias com marcação, dias sem registro, faltas injustificadas e atestados do mês, com exportação em CSV para o fechamento do pagamento, e a folha mensal de cada pessoa com os pedidos de correção pendentes. A consulta não SHALL expor atestado, motivo clínico, CPF, salário ou dados bancários.

#### Scenario: Gestor consulta a folha da equipe
- **WHEN** um superior direto ou Gestor abre a folha de ponto de um mês
- **THEN** o sistema retorna só as pessoas no seu escopo, com o resumo do mês de cada uma

#### Scenario: RH fecha o mês
- **WHEN** RH ou Admin consulta a folha de um mês encerrado
- **THEN** o sistema retorna todas as pessoas, com filtro por departamento, e permite baixar o resumo em CSV

#### Scenario: Pessoa fora do escopo
- **WHEN** alguém pede a folha de uma pessoa que não está no seu escopo
- **THEN** o sistema nega o acesso

### Requirement: Prazo para pedir correção de ponto
O sistema SHALL manter um prazo, em dias, para o colaborador pedir a correção de um dia de ponto, definido por RH ou Admin: de 1 a 3650 dias, ou sem limite, que é o valor inicial. Com prazo definido, o pedido de correção de um dia anterior a hoje menos o prazo (data de Brasília) SHALL ser recusado com mensagem que oriente a procurar o gestor ou o RH. O ajuste direto feito por quem decide pela hierarquia não SHALL ter prazo. A alteração do prazo SHALL ser auditada, e o prazo atual SHALL estar disponível para consulta de qualquer usuário autenticado.

#### Scenario: Pedido dentro do prazo
- **WHEN** o colaborador pede a correção de um dia que ainda está dentro do prazo
- **THEN** o sistema aceita o pedido conforme as demais regras de correção

#### Scenario: Pedido fora do prazo
- **WHEN** o colaborador pede a correção de um dia anterior a hoje menos o prazo
- **THEN** o sistema recusa o pedido com mensagem que orienta a falar com o gestor ou o RH, e o espelho mostra o dia sem a ação de correção

#### Scenario: RH altera o prazo
- **WHEN** RH ou Admin define o prazo em dias ou volta para sem limite
- **THEN** o sistema grava o novo prazo, registra a alteração na auditoria e passa a aplicá-lo aos novos pedidos

#### Scenario: Prazo alterado por quem não é RH
- **WHEN** um Colaborador ou Gestor tenta alterar o prazo
- **THEN** o sistema nega a alteração

### Requirement: Benefícios do colaborador
O sistema SHALL manter um catálogo de benefícios cadastrado por RH ou Admin (nome único, tipo, operadora e descrição), que pode ser ativado ou desativado; benefício desativado não SHALL aceitar novos vínculos, e os vínculos atuais continuam. RH ou Admin SHALL poder vincular um benefício ativo a um colaborador não desligado, com valor pago pela empresa, desconto do colaborador e vigência, sem dois vínculos vigentes do mesmo benefício para a mesma pessoa e com o fim não anterior ao início. Encerrar um vínculo SHALL preencher o fim sem apagar o histórico. O colaborador SHALL consultar somente os próprios benefícios, ativos e encerrados, com os totais do mês. Todas as escritas SHALL ser auditadas.

#### Scenario: Colaborador consulta os benefícios
- **WHEN** um colaborador abre os seus benefícios
- **THEN** o sistema mostra só os dele, com tipo, operadora, valor da empresa, desconto e vigência, e os totais dos ativos

#### Scenario: RH vincula um benefício
- **WHEN** RH vincula um benefício ativo a um colaborador ativo, com valores e início
- **THEN** o sistema grava o vínculo e registra a ação na auditoria

#### Scenario: Vínculo repetido
- **WHEN** RH tenta vincular um benefício que a pessoa já tem vigente
- **THEN** o sistema recusa o vínculo com mensagem clara

#### Scenario: Encerrar sem apagar
- **WHEN** RH encerra um vínculo
- **THEN** o sistema preenche o fim, mantém o histórico e o benefício deixa de contar nos totais do mês

### Requirement: Vínculo de conta a ficha de colaborador
O sistema SHALL permitir ligar uma conta de acesso que não tem ficha de colaborador a uma ficha que não tem conta, de colaborador não desligado, para que a pessoa use as funções de funcionário (ponto, férias, pagamento). O Admin SHALL poder vincular qualquer conta; o RH, só contas de perfil Colaborador. Ninguém SHALL vincular a própria conta. O vínculo SHALL ser auditado.

#### Scenario: Conta vinculada
- **WHEN** o Admin liga uma conta sem ficha a uma ficha sem conta, de colaborador ativo
- **THEN** o sistema grava o vínculo, registra a ação na auditoria e a pessoa passa a ter acesso às funções de funcionário

#### Scenario: Vínculo recusado
- **WHEN** alguém tenta vincular a própria conta, uma conta que já tem ficha ou uma ficha que já tem conta
- **THEN** o sistema recusa o vínculo com mensagem clara
