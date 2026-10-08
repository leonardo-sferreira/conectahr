# conectahr Specification

## Purpose
Define o comportamento funcional e as regras de seguranca da plataforma ConectaRH para centralizar processos de pessoas, jornada, documentos, ausencias e desenvolvimento de colaboradores.

## Requirements

### Requirement: Autenticacao e ciclo de sessao
O sistema SHALL autenticar usuarios por credencial e emitir token de acesso com validade de uma hora, vinculado a um registro de sessao criado no mesmo momento. O sistema SHALL invalidar no logout exatamente a sessao do token usado, sem encerrar sessoes de outros dispositivos, exigir nova autenticacao apos a saida e impedir o acesso com token expirado, revogado, adulterado ou de sessao encerrada. O sistema SHALL recusar requisicoes de usuario inativo mesmo com token ainda valido.

#### Scenario: Login valido
- **WHEN** um usuario ativo informa credenciais validas
- **THEN** o sistema emite uma sessao com token valido por uma hora, vinculado ao registro da sessao, e registra o ultimo acesso

#### Scenario: Token expirado ou revogado
- **WHEN** uma requisicao usa token expirado, revogado, invalido ou de sessao encerrada
- **THEN** o sistema rejeita a requisicao e exige nova autenticacao

#### Scenario: Logout encerra somente a sessao atual
- **WHEN** um usuario com sessoes em dois dispositivos faz logout em um deles
- **THEN** o token daquele dispositivo passa a ser recusado e o token do outro dispositivo continua valido

### Requirement: Primeiro acesso, redefinicao e validacao de login por e-mail
O sistema SHALL permitir que somente Admin ou RH cadastrem usuarios. O sistema SHALL marcar credenciais temporarias, obrigar a troca antes de liberar o uso normal e permitir redefinicao iniciada na tela de login. A validacao padrao de todo login, apos e-mail e senha corretos, SHALL ser um codigo numerico de 6 digitos enviado por e-mail, valido por 5 minutos, exigido antes de emitir a sessao. O sistema SHALL bloquear a validacao do codigo apos 5 tentativas invalidas, descartando o codigo e exigindo novo login para gerar outro. O sistema SHALL permitir reenviar um novo codigo que substitui o anterior somente enquanto houver menos de 5 tentativas invalidas, sem zerar a contagem de tentativas, respeitando um intervalo minimo de 60 segundos entre reenvios e um limite de 3 reenvios por login.

#### Scenario: Primeiro acesso com senha temporaria
- **WHEN** o usuario autentica com senha temporaria
- **THEN** o sistema libera somente a troca de senha, a consulta do proprio usuario, o logout e as rotas de sessao, e nega todos os demais modulos ate a conclusao da troca

#### Scenario: Login exige codigo por e-mail
- **WHEN** o usuario informa e-mail e senha validos
- **THEN** o sistema envia um codigo de 6 digitos por e-mail e so emite a sessao apos o codigo correto ser informado

#### Scenario: Codigo expirado ou com tentativas esgotadas
- **WHEN** o codigo informado esta expirado ou o usuario ja errou 5 vezes
- **THEN** o sistema recusa a validacao sem revelar qual condicao falhou e exige um novo login para gerar outro codigo

#### Scenario: Reenvio apos tentativas esgotadas
- **WHEN** o usuario ja errou o codigo 5 vezes e pede reenvio
- **THEN** o sistema recusa o reenvio e so um novo login com senha gera outro codigo

#### Scenario: Reenvio antes do intervalo ou acima do limite
- **WHEN** o usuario pede reenvio menos de 60 segundos apos o ultimo envio, ou ja usou os 3 reenvios do login
- **THEN** o sistema recusa o reenvio sem enviar e-mail e sem alterar o codigo vigente

#### Scenario: Redefinicao solicitada no login
- **WHEN** o usuario solicita redefinicao para um e-mail cadastrado e ativo
- **THEN** o sistema envia um fluxo de redefinicao com token de uso unico e prazo limitado sem revelar se o e-mail existe

### Requirement: Sessoes e dispositivos
O sistema SHALL permitir consultar sessoes ativas, ultimo acesso, dispositivo ou navegador, tentativas recentes e encerrar uma sessao ou todas as demais. Encerrar uma sessao SHALL revogar de fato o token correspondente. "Todas as demais" SHALL significar todas exceto a sessao do token usado na requisicao. A desativacao de um usuario e a conclusao do desligamento do colaborador vinculado SHALL revogar todas as sessoes desse usuario. O sistema SHALL alertar acessos suspeitos.

#### Scenario: Encerramento de dispositivo
- **WHEN** o usuario encerra uma sessao especifica
- **THEN** o token daquela sessao e revogado sem encerrar as demais

#### Scenario: Encerrar as demais sessoes
- **WHEN** o usuario encerra todas as outras sessoes
- **THEN** os tokens das outras sessoes passam a ser recusados e o token usado na requisicao continua valido

#### Scenario: Desativacao revoga sessoes
- **WHEN** RH desativa um usuario ou conclui o desligamento do colaborador vinculado
- **THEN** todas as sessoes do usuario sao revogadas e qualquer token emitido antes passa a ser recusado

### Requirement: Autorizacao por perfil e estrutura organizacional
O sistema SHALL aplicar permissoes por perfil Admin, RH, Gestor ou Colaborador, restringindo dados conforme o escopo do usuario. O sistema SHALL permitir vincular cada colaborador a um gestor e cada gestor a uma unica area/departamento, impedindo acesso fora do escopo autorizado.

#### Scenario: Colaborador consulta os proprios dados
- **WHEN** um Colaborador acessa um recurso pessoal
- **THEN** o sistema permite apenas seus proprios dados e operacoes explicitamente autorizadas

#### Scenario: Gestor consulta sua equipe
- **WHEN** um Gestor acessa colaboradores vinculados a sua area
- **THEN** o sistema retorna somente sua equipe e permite apenas decisoes previstas para o papel

#### Scenario: Acesso administrativo
- **WHEN** Admin ou RH acessa a gestao organizacional
- **THEN** o sistema permite as operacoes administrativas conforme suas permissoes e registra a acao

### Requirement: Organograma da empresa
O sistema SHALL apresentar uma visualizacao hierarquica da estrutura organizacional, reunindo departamentos, gestores e colaboradores vinculados, a partir dos dados ja mantidos de cargo, departamento e vinculo gestor-colaborador. O organograma SHALL incluir todo colaborador cujo status nao seja `Desligado`, inclusive quem estiver de ferias ou afastado. O sistema SHALL restringir a visualizacao a nome, cargo e departamento de cada pessoa, sem expor dados sensiveis.

#### Scenario: Consulta do organograma
- **WHEN** um usuario autenticado acessa o organograma
- **THEN** o sistema exibe departamentos, gestores e colaboradores em estrutura hierarquica, mostrando apenas nome, cargo e departamento de cada pessoa

#### Scenario: Colaborador de ferias no organograma
- **WHEN** um colaborador esta com status `Ferias` ou `Afastado`
- **THEN** ele continua aparecendo no organograma; somente colaboradores `Desligado` sao omitidos

### Requirement: Pesquisa global de colaboradores
O sistema SHALL permitir buscar colaboradores por nome, CPF, matricula (id), cargo ou departamento, retornando somente os registros dentro do escopo de acesso do usuario que pesquisa.

#### Scenario: Busca dentro do escopo
- **WHEN** um Gestor pesquisa colaboradores
- **THEN** o sistema retorna apenas resultados da sua equipe; RH e Admin recebem resultados de qualquer colaborador ativo

**3. Cadastro, Histórico Profissional e Desligamento**

### Requirement: Cadastro e historico profissional
O sistema SHALL manter usuarios, colaboradores, cargos, departamentos e historico profissional, incluindo admissao, promocoes, alteracoes de departamento, salario, cargo, contrato e desligamento. O sistema SHALL validar os dominios informados: contratos CLT, PJ, ESTAGIO, APRENDIZ, TEMPORARIO e OUTRO; status Ativo, Ferias, Afastado e Desligado; e niveis l1 a l5.

O sistema SHALL permitir que o colaborador cadastre e atualize seus proprios dados bancarios — banco, agencia, conta, digito e tipo de conta (corrente ou poupanca) — vinculados ao seu cadastro. RH e Admin SHALL poder consultar esses dados para fins de pagamento, sem edita-los em nome do colaborador; Gestor nao SHALL visualizar dados bancarios de sua equipe.

#### Scenario: Alteracao profissional
- **WHEN** RH registra uma alteracao de cargo, salario, contrato ou departamento
- **THEN** o sistema atualiza o cadastro, cria um evento no historico com responsavel e preserva os valores anteriores

#### Scenario: Valor fora do dominio
- **WHEN** uma operacao informa tipo de contrato, status ou nivel nao permitido
- **THEN** o sistema rejeita a operacao com erro de validacao

#### Scenario: Colaborador cadastra dados bancarios
- **WHEN** um colaborador informa banco, agencia, conta, digito e tipo de conta validos
- **THEN** o sistema salva os dados vinculados ao seu cadastro e permite atualiza-los a qualquer momento

#### Scenario: Dados bancarios fora do dominio
- **WHEN** o tipo de conta informado nao e corrente nem poupanca, ou campos obrigatorios estao ausentes
- **THEN** o sistema rejeita a operacao com erro de validacao

#### Scenario: RH consulta dados bancarios para pagamento
- **WHEN** RH ou Admin consulta o cadastro de um colaborador para processar pagamento
- **THEN** o sistema exibe os dados bancarios vigentes sem permitir edicao por RH ou Admin

#### Scenario: Gestor sem acesso aos dados bancarios
- **WHEN** um Gestor consulta os dados de um colaborador da sua equipe
- **THEN** o sistema oculta os dados bancarios, visiveis somente ao proprio colaborador, RH e Admin

### Requirement: Validação local de CPF
O sistema SHALL normalizar o CPF removendo caracteres não numéricos, exigir onze dígitos, rejeitar sequências com o mesmo dígito e validar os dois dígitos verificadores sem consultar serviço externo.

#### Scenario: CPF com máscara válido
- **WHEN** o usuário informa um CPF formatado com pontos e hífen que passa nos dígitos verificadores
- **THEN** o sistema normaliza o valor e aceita o CPF após a validação local

#### Scenario: CPF repetido ou inválido
- **WHEN** o CPF possui sequência repetida, quantidade incorreta ou dígitos verificadores inválidos
- **THEN** o sistema rejeita o valor sem chamar o serviço externo

### Requirement: Admissao e contrato CLT
O sistema SHALL exigir cadastro contratual completo para colaborador CLT, incluindo cargo, salario, jornada, departamento e data de admissao, validar CPF e datas e impedir inicio operacional antes do registro exigido. Alteracoes contratuais SHALL gerar historico, vigencia e responsavel. Integracoes com eSocial e CTPS Digital SHALL registrar estado da comunicacao e prazos aplicaveis sem mascarar indisponibilidade externa.

#### Scenario: CLT sem registro
- **WHEN** uma admissao CLT nao possui registro confirmado ou estado de comunicacao valido
- **THEN** o sistema impede o inicio operacional e sinaliza a pendencia para RH

#### Scenario: Alteracao contratual
- **WHEN** RH altera cargo, salario, jornada, contrato ou departamento
- **THEN** o sistema cria nova vigencia, preserva o historico anterior e registra o responsavel

### Requirement: Desligamento de colaborador
O sistema SHALL permitir que Colaborador ou Gestor solicitem o desligamento de um colaborador dentro do proprio escopo (a si mesmo ou a colaboradores do departamento sob sua gestao), com decisao exclusiva do RH, que nao pode decidir uma solicitacao em que ele mesmo e o colaborador. O sistema SHALL suportar desligamento `imediato` e `aviso_previo`, bloquear nova solicitacao enquanto existir uma pendente, em analise ou agendada para o mesmo colaborador, e concluir os desligamentos agendados cuja data efetiva foi atingida, seja pela conclusao manual do RH, seja pela rotina diaria acionada manualmente.

#### Scenario: Solicitacao dentro do escopo
- **WHEN** um Colaborador solicita o proprio desligamento ou um Gestor solicita o desligamento de um colaborador do seu departamento
- **THEN** o sistema cria a solicitacao como `pendente` e impede solicitacao para colaborador fora do escopo do solicitante

#### Scenario: Aprovacao exclusiva do RH
- **WHEN** RH aprova uma solicitacao em analise de outro colaborador
- **THEN** o sistema conclui o desligamento imediato ou agenda a data efetiva para aviso previo, conforme o tipo da solicitacao

#### Scenario: Conclusao do desligamento
- **WHEN** um desligamento imediato e aprovado, ou um desligamento agendado com data efetiva atingida e concluido pelo RH ou pela rotina diaria
- **THEN** o sistema atualiza o status do colaborador para Desligado, desativa o acesso do usuario vinculado, revoga todas as suas sessoes e registra o evento no historico profissional

#### Scenario: Solicitacao duplicada
- **WHEN** ja existe uma solicitacao pendente, em analise ou agendada para o colaborador
- **THEN** o sistema rejeita a criacao de uma nova solicitacao para o mesmo colaborador

### Requirement: Informacoes derivadas do cadastro
O sistema SHALL calcular e exibir, a partir dos dados ja cadastrados, o tempo de empresa de cada colaborador desde a `data_admissao` e a lista de aniversariantes do mes corrente com base em `data_nascimento`, considerando todo colaborador cujo status nao seja `Desligado` e respeitando o escopo de acesso do usuario. O sistema SHALL apresentar uma timeline do colaborador reunindo, em ordem cronologica, os eventos de `historico_profissional` (admissao, promocoes, alteracoes de cargo, departamento ou contrato, desligamento), ferias concluidas e avaliacoes concluidas.

#### Scenario: Tempo de empresa exibido
- **WHEN** colaborador ou RH consulta o cadastro
- **THEN** o sistema exibe o tempo de empresa calculado a partir da data de admissao

#### Scenario: Aniversariantes do mes
- **WHEN** um usuario autenticado acessa o painel de aniversariantes
- **THEN** o sistema lista os colaboradores nao desligados, inclusive de ferias ou afastados, que fazem aniversario no mes corrente, respeitando o escopo de acesso

#### Scenario: Timeline consultada
- **WHEN** colaborador ou gestor autorizado consulta a timeline de um colaborador
- **THEN** o sistema exibe os eventos do historico profissional, ferias concluidas e avaliacoes concluidas em ordem cronologica

### Requirement: Regras de jornada e ferias por contrato
O sistema SHALL aplicar regras de jornada e ferias conforme o tipo de contrato do colaborador, incluindo CLT, PJ, ESTAGIO, APRENDIZ, TEMPORARIO e OUTRO. A configuracao SHALL ser parametrizavel e o sistema SHALL validar o contrato antes de calcular jornada, horas extras, elegibilidade ou periodo de ferias.

A configuracao inicial SHALL seguir esta matriz:

| Tipo de contrato | Horas/dia | Horas/semana | Periodo aquisitivo | Ferias/recesso | Proporcional | Solicita no sistema | Fracionamento |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CLT` | 8 | 44 | 12 meses | 30 dias | Sim | Sim | Ate 3 periodos |
| `PJ` | Nao aplicar | Nao aplicar | Nao aplicar | Nao aplicar | Nao | Nao | Nao aplicar |
| `ESTAGIO` | 6 | 30 | 12 meses | 30 dias de recesso | Sim | Sim | 1 periodo |
| `APRENDIZ` | 6 | 30 | 12 meses | 30 dias | Sim | Sim | 1 periodo |
| `TEMPORARIO` | 8 | 44 | Nao aplicar | Ferias proporcionais | Sim | Nao, por padrao | Nao aplicar |
| `OUTRO` | Configuracao manual | Configuracao manual | Configuracao manual | Configuracao manual | Configuracao manual | Configuracao manual | Configuracao manual |

As regras deverao aceitar ajustes autorizados para contrato, acordo ou norma aplicavel sem alterar retroativamente calculos ja registrados.

#### Scenario: Jornada calculada por contrato
- **WHEN** o sistema calcula a jornada de colaboradores com tipos de contrato diferentes
- **THEN** aplica a regra correspondente a cada contrato e informa o resultado conforme sua parametrizacao

#### Scenario: Ferias validadas por contrato
- **WHEN** um colaborador solicita ferias
- **THEN** o sistema valida elegibilidade, periodo e quantidade de dias usando a regra do seu tipo de contrato

#### Scenario: Contrato sem solicitacao de ferias
- **WHEN** um colaborador PJ ou temporario tenta solicitar ferias e a configuracao nao permite a solicitacao
- **THEN** o sistema bloqueia a solicitacao e informa que o fluxo deve ser tratado conforme a regra contratual configurada

#### Scenario: Contrato OUTRO configurado manualmente
- **WHEN** RH configura os parametros de um colaborador com contrato OUTRO
- **THEN** o sistema usa os valores manuais para jornada, elegibilidade, proporcionalidade, solicitacao e fracionamento

### Requirement: Jornada, intervalos e banco de horas CLT
O sistema SHALL respeitar os limites configurados e formalmente aprovados para jornada CLT, incluindo ate 8 horas diarias, ate 44 semanais, horas extras, adicional minimo aplicavel, descanso entre jornadas, repouso semanal, trabalho noturno e intervalos. Jornada acima de 6 horas SHALL exigir intervalo configurado normalmente de ao menos 1 hora; jornada acima de 4 e ate 6 horas SHALL considerar 15 minutos pela regra geral. O sistema nao SHALL preencher intervalo como realizado sem marcacao. Banco de horas SHALL exigir fundamento, origem, limites, compensacao e tratamento de saldo.

#### Scenario: Intervalo nao marcado
- **WHEN** uma jornada exige intervalo mas nao possui marcacao de saida e retorno
- **THEN** o sistema nao inventa o intervalo e sinaliza a inconsistência para tratamento autorizado

#### Scenario: Banco sem fundamento
- **WHEN** alguem tenta habilitar banco de horas sem instrumento aplicavel aprovado
- **THEN** o sistema bloqueia a ativacao e solicita fundamento normativo

### Requirement: Estagio, aprendizagem, trabalho temporario e PJ
O sistema SHALL exigir termo de compromisso para estagio e manter estudante, instituicao de ensino, jornada, recesso e proporcionalidade sem classificar o estagiario como CLT. O sistema SHALL limitar aprendiz conforme contrato e programa, somar atividades praticas e teoricas, impedir horas extras ou compensacao indevida e aplicar protecoes de menor. Trabalho temporario SHALL exigir contrato escrito, empresa, tomadora, motivo, prazo e prorrogacoes. PJ SHALL nao receber automaticamente jornada, ponto, ferias ou subordinacao de empregado e SHALL manter contrato, entregas, vigencia e condicoes comerciais.

#### Scenario: Cadastro de estagio sem termo
- **WHEN** RH tenta ativar estagio sem termo de compromisso valido
- **THEN** o sistema bloqueia a ativacao e exibe a pendencia documental

#### Scenario: Jornada de aprendiz excedente
- **WHEN** uma jornada de aprendiz excede o limite aplicavel sem fundamento permitido
- **THEN** o sistema rejeita o registro e informa a regra violada

#### Scenario: PJ com férias trabalhistas
- **WHEN** alguem tenta criar ferias trabalhistas para prestador PJ sem regra contratual especifica
- **THEN** o sistema bloqueia a operação e direciona para o contrato comercial

### Requirement: Ponto experimental e conformidade futura
O sistema SHALL identificar o registro de ponto do MVP como controle interno experimental, preservar marcacoes originais, separar ajustes, disponibilizar espelho ao trabalhador e registrar solicitante, aprovador e justificativa. O sistema nao SHALL declarar conformidade como REP-P, REP-A ou REP-C sem implementacao e validacao especificas da Portaria nº 671/2021.

#### Scenario: Marcacao preservada
- **WHEN** uma correcao de ponto e solicitada ou aprovada
- **THEN** a marcacao original permanece imutavel e o ajuste fica em registro separado

#### Scenario: Espelho do trabalhador
- **WHEN** o colaborador consulta seu ponto
- **THEN** o sistema disponibiliza o espelho e diferencia marcacoes originais, ajustes e decisoes

### Requirement: Registro de ponto e correcao
O sistema SHALL permitir registrar entrada, inicio e fim de intervalo e saida, acompanhar a jornada e calcular horas trabalhadas e extras quando aplicavel. O registro SHALL usar os status ABERTO, COMPLETO, INCOMPLETO ou AJUSTADO; um registro ABERTO de dia anterior SHALL passar a INCOMPLETO quando a rotina diaria for acionada. O colaborador SHALL poder solicitar correcao, e o responsavel autorizado (RH, Admin, o Gestor do departamento do colaborador ou o substituto de uma delegacao vigente desse Gestor) SHALL poder aprovar ou recusar com justificativa, nunca sobre o proprio registro.

#### Scenario: Jornada concluida
- **WHEN** o colaborador registra os marcadores necessarios do dia
- **THEN** o sistema calcula a jornada e marca o registro como COMPLETO

#### Scenario: Correcao aprovada
- **WHEN** o responsavel com permissao aprova uma solicitacao de correcao de outro colaborador
- **THEN** o sistema ajusta o registro, preserva o valor original, registra a decisao e marca o registro como AJUSTADO

#### Scenario: Jornada nao finalizada
- **WHEN** RH aciona a rotina diaria e existe registro ABERTO de um dia anterior
- **THEN** o sistema marca o registro como INCOMPLETO sem inventar marcacoes ausentes

### Requirement: Regras contratuais e excecoes individuais
O sistema SHALL permitir que regras de jornada e ferias sejam administradas por tipo de contrato com horas diarias, horas semanais, periodo aquisitivo, dias, proporcionalidade, fracionamento, limite de periodos, antecedencia, obrigatoriedade de ponto, habilitacao de solicitacao e vigencia inicial e final. O sistema SHALL permitir excecoes individuais auditadas com jornada, escala, horas, ferias, vigencia, justificativa e autorizador.

#### Scenario: Regra vigente aplicada
- **WHEN** o sistema calcula jornada ou valida ferias
- **THEN** usa a regra contratual vigente na data do evento, sem alterar calculos historicos

#### Scenario: Excecao individual aplicada
- **WHEN** RH autoriza uma excecao para um colaborador dentro de sua vigencia
- **THEN** o sistema aplica a excecao, preserva a regra original e registra justificativa e autorizador

**5. Instrumentos Normativos e Regras Override**

### Requirement: Instrumentos normativos e regras override
O sistema SHALL manter a entidade `instrumento_normativo` com tipo `acordo_coletivo`, `convencao_coletiva`, `termo_aditivo`, `regime_especial`, `norma_legal`, `decisao_judicial` ou `acordo_individual_autorizado`; titulo, descricao, entidade responsavel, categoria profissional, abrangencia territorial, vigencia, documento, hash, observacao, status e responsaveis. O status SHALL ser `rascunho`, `pendente_aprovacao`, `vigente`, `suspenso`, `expirado`, `revogado` ou `rejeitado`.

O sistema SHALL manter `regra_override` como regra versionada, nunca como alteracao direta no colaborador. Cada override SHALL registrar instrumento de origem, parametro, valor anterior, valor novo, prioridade, abrangencia, referencias opcionais, vigencia, justificativa e ativo. Os parametros permitidos SHALL incluir jornada, intervalo, horas extras, banco de horas, ponto, ferias, fracionamento, antecedencia e solicitacao de ferias.

Instrumentos coletivos SHALL armazenar `numero_solicitacao_mediador` no formato `^MR[0-9]{5,6}/[0-9]{4}$`, `numero_registro_mte` no formato `^[A-Z]{2}[0-9]{6}/[0-9]{4}$` e `numero_processo_mte` no formato `^[0-9]{5}\.[0-9]{6}/[0-9]{4}-[0-9]{2}$`. Termos aditivos SHALL armazenar instrumento principal, seus identificadores e clausulas alteradas.

#### Scenario: Instrumento enviado para aprovacao
- **WHEN** RH cadastra um instrumento com documento comprobatório
- **THEN** o sistema cria o instrumento como `pendente_aprovacao` e impede sua aplicação até aprovação por Admin ou responsável autorizado

#### Scenario: Autor tenta autoaprovar
- **WHEN** o usuário que criou o instrumento tenta aprová-lo
- **THEN** o sistema bloqueia a ação e mantém o instrumento pendente

#### Scenario: Nova versão de regra
- **WHEN** uma regra vigente precisa ser alterada
- **THEN** o sistema cria nova versão, preserva a anterior e impede sobrescrita

#### Scenario: Identificador inválido
- **WHEN** um identificador Mediador, MTE ou processo não respeita o formato do tipo correspondente
- **THEN** o sistema rejeita o instrumento e informa o campo inválido

#### Scenario: Instrumento coletivo sem registro
- **WHEN** acordo coletivo, convenção coletiva ou termo aditivo não possui registro no MTE, documento oficial ou aprovação interna
- **THEN** o sistema mantém o instrumento como `pendente_aprovacao` e impede a ativação

#### Scenario: Instrumento coletivo ativado
- **WHEN** o instrumento coletivo possui solicitação, registro, processo, data de registro, vigência, categoria, abrangência, documento e aprovação
- **THEN** o sistema permite a transição para `vigente`

### Requirement: Abrangencia e resolução de regras
O campo `regra_override.abrangencia` SHALL aceitar `empresa`, `estabelecimento`, `estado`, `municipio`, `departamento`, `cargo`, `tipo_contrato`, `categoria_profissional` ou `colaborador`, com referências compatíveis. A resolução SHALL considerar, nesta ordem, matriz do contrato, norma vigente, instrumento coletivo, regra de cargo/departamento e exceção individual. Em conflito, SHALL considerar vigência, abrangência, prioridade e especificidade; conflito não resolvido SHALL bloquear a publicação e exigir análise humana.

#### Scenario: Override aplicável
- **WHEN** uma jornada ou férias é calculada para colaborador abrangido por regra vigente
- **THEN** o sistema aplica a regra resolvida de maior prioridade e especificidade

#### Scenario: Conflito jurídico
- **WHEN** duas regras vigentes entram em conflito sem resolução aprovada
- **THEN** o sistema bloqueia a publicação e encaminha o caso para RH ou responsável jurídico

### Requirement: Aprovação, simulação e aplicação versionada
O sistema SHALL permitir simular um override antes da publicação, exibindo colaboradores afetados, escopos, regra atual, regra nova, conflitos, início de vigência e processos futuros afetados. Ao calcular jornada, ponto ou férias, SHALL gravar regra aplicada, versão, instrumento, parâmetros e data do cálculo. Regras retroativas SHALL exigir justificativa e aprovação especial, e registros anteriores SHALL preservar a regra usada. A expiração de instrumentos por fim de vigência SHALL ocorrer quando RH ou Admin acionar a rotina diária.

#### Scenario: Simulação antes da publicação
- **WHEN** RH solicita simulação de um override
- **THEN** o sistema apresenta o impacto previsto sem alterar regras vigentes

#### Scenario: Cálculo auditável
- **WHEN** o sistema conclui um cálculo de jornada, ponto ou férias
- **THEN** armazena a regra, versão, instrumento, parâmetros e data utilizados

#### Scenario: Instrumento expirado
- **WHEN** RH aciona a rotina diária e a vigência de um instrumento `vigente` já terminou
- **THEN** o sistema marca-o como `expirado` e deixa de usá-lo em novos cálculos sem alterar registros anteriores

### Requirement: Ferias e ausencias
O sistema SHALL permitir solicitar ferias e registrar ausencias com acompanhamento de status. Ferias SHALL usar Pendente, Aprovada, Rejeitada, Cancelada ou Concluida. Ausencias SHALL usar Falta, Atestado, Afastamento, Licenca ou Outro e status Pendente, Aprovada, Rejeitada ou Registrado. RH e Admin SHALL decidir ferias de qualquer colaborador; o Gestor SHALL decidir ferias somente de colaboradores do departamento que gerencia; o substituto de uma delegacao vigente do Gestor com escopo `ferias` ou `todas` SHALL decidir dentro do mesmo escopo. Ninguem SHALL decidir as proprias ferias. Toda decisao SHALL manter justificativa e responsavel. Nas ausencias, o Gestor SHALL consultar somente tipo, periodo e status das ausencias da equipe, sem acesso ao atestado ou documento anexado.

#### Scenario: Ferias aprovadas
- **WHEN** RH, Admin, Gestor do departamento ou substituto com delegacao vigente aprova uma solicitacao pendente de outro colaborador
- **THEN** o sistema valida o periodo, registra a decisao e o responsavel e altera o status para Aprovada

#### Scenario: Gestor fora do escopo
- **WHEN** um Gestor tenta decidir ferias de colaborador de outro departamento
- **THEN** o sistema nega a decisao

#### Scenario: Ausencia registrada
- **WHEN** uma ausencia e criada com tipo permitido e periodo valido
- **THEN** o sistema registra o evento e apresenta seu status conforme o fluxo aplicavel

#### Scenario: Gestor consulta ausencia da equipe
- **WHEN** um Gestor consulta as ausencias de um colaborador da sua equipe
- **THEN** o sistema retorna tipo, periodo e status, sem atestado, documento ou motivo clinico

### Requirement: Delegacao, prazos e calendario
O sistema SHALL suportar delegacao temporaria de aprovacao, com titular, substituto, vigencia, permissoes, motivo e bloqueio de autoaprovacao. Uma delegacao SHALL ser considerada vigente quando a data atual estiver entre `data_inicio` e `data_fim` e ela nao tiver sido cancelada; fora disso ela deixa de valer sem nenhuma rotina de expiracao. No MVP, a delegacao SHALL ser aplicada nas decisoes de ferias e de correcao de ponto. O sistema SHALL controlar prazos e escalonar atrasos. O calendario SHALL reunir feriados, dias nao uteis, ferias, ausencias, ciclos, vencimentos e prazos e ser considerado nos calculos aplicaveis.

#### Scenario: Delegacao vigente
- **WHEN** o substituto decide ferias ou correcao de ponto de colaborador da equipe do titular durante uma delegacao vigente com escopo compativel
- **THEN** o sistema permite a decisao e registra titular, substituto e decisao

#### Scenario: Delegacao vencida ou cancelada
- **WHEN** o substituto tenta decidir apos a `data_fim` ou apos o cancelamento da delegacao
- **THEN** o sistema nega a decisao

#### Scenario: Prazo vencido
- **WHEN** uma pendencia ultrapassa seu prazo
- **THEN** o sistema marca como atrasada, notifica o responsavel e escalona ao nivel superior quando configurado

#### Scenario: Conflito de ferias
- **WHEN** uma ferias e analisada
- **THEN** o sistema verifica sobreposicoes, ausencias, saldo, antecedencia, periodo aquisitivo e disponibilidade minima da equipe e gera alerta conforme a politica

### Requirement: Documentos e pendencias
O sistema SHALL permitir que colaboradores enviem documentos associados ao seu cadastro e que RH solicite documentos pendentes. O sistema SHALL manter tipo, metadados, validade, observacoes, estado e responsaveis, proteger os arquivos e notificar pendencias por e-mail. `documento.status` SHALL aceitar somente `pendente_analise`, `aprovado`, `rejeitado`, `vencido`, `substituido` ou `arquivado`. RH SHALL poder processar documentos `aprovado` cuja `data_validade` terminou, alterando-os para `vencido`. O documento vencido SHALL deixar de ser valido, permanecer armazenado e nao SHALL desativar o colaborador. `documento.tipo` SHALL incluir tambem `holerite` e `informe_rendimentos` para documentos emitidos pelo RH. Documentos desse tipo SHALL ser criados ja como `aprovado`, sem passar por `pendente_analise`, pois o RH e a fonte da informacao.

#### Scenario: Documento enviado
- **WHEN** um colaborador envia um arquivo permitido para um tipo de documento
- **THEN** o sistema armazena o arquivo protegido, associa-o ao colaborador e informa o recebimento

#### Scenario: Documento emitido pelo RH
- **WHEN** RH anexa um holerite ou informe de rendimentos para um colaborador
- **THEN** o sistema cria o documento com status `aprovado`, disponivel para download pelo proprio colaborador, sem exigir analise adicional

#### Scenario: Pendencia solicitada
- **WHEN** RH solicita um documento ausente ou vencido
- **THEN** o sistema cria a pendencia, define prazo e envia notificacao ao colaborador

#### Scenario: Documento aprovado vencido
- **WHEN** RH processa vencimentos e encontra um documento aprovado cuja data de validade terminou
- **THEN** altera o status para `vencido`, preserva o arquivo e sinaliza a necessidade de substituicao sem alterar o status do colaborador

#### Scenario: Alertas de vencimento
- **WHEN** RH processa vencimentos e um documento aprovado esta a 30, 15 ou 7 dias da data de validade, ou no dia do vencimento
- **THEN** o sistema envia o alerta correspondente por e-mail, sem repetir um alerta ja enviado para o mesmo limiar

#### Scenario: Documento substituido ou arquivado
- **WHEN** RH ou colaborador autorizado envia uma substituicao ou arquiva um documento vencido
- **THEN** o sistema preserva o documento anterior, registra a relacao ou motivo e atualiza o status permitido

### Requirement: Quarentena e retencao de documentos
O sistema SHALL processar anexos pelos estados `enviado`, `em_verificacao`, `liberado` ou `bloqueado`, validando extensao, tipo real, tamanho, hash, duplicidade, corrupcao e verificacao de seguranca antes da liberacao. O sistema SHALL manter politica de retencao por tipo de documento com finalidade, base, prazo, evento inicial, tratamento, anonimização, eliminacao ou revisao e bloqueio por processo. Cada documento SHALL registrar a data ate a qual deve ser retido, e RH ou Admin SHALL dispor de uma listagem dos documentos com retencao vencida para revisao manual. No MVP, nenhum documento SHALL ser eliminado automaticamente.

#### Scenario: Arquivo liberado
- **WHEN** o anexo passa por todas as verificacoes
- **THEN** o sistema altera o estado para `liberado` e permite seu uso conforme permissao

#### Scenario: Arquivo bloqueado
- **WHEN** o anexo falha em uma verificacao de seguranca ou integridade
- **THEN** o sistema altera o estado para `bloqueado`, impede o uso e registra o motivo

#### Scenario: Retencao impede eliminacao
- **WHEN** um documento esta sob bloqueio de processo ou revisao manual
- **THEN** o sistema impede a eliminacao automatica e preserva o historico

#### Scenario: Revisao de retencao vencida
- **WHEN** RH consulta a listagem de retencao
- **THEN** o sistema lista os documentos cuja data de retencao ja passou, sem alterar nem eliminar nenhum deles

### Requirement: Protecao de dados pessoais, saude e ausencias
O sistema SHALL coletar somente documentos necessarios, informar finalidade, restringir acesso por perfil e necessidade, usar armazenamento privado e aplicar retencao conforme finalidade e obrigacao legal. Atestados, ASO, dados biometricos e filiação sindical SHALL ter protecao de dados sensiveis. Gestores SHALL visualizar somente informacao operacional necessaria, e o sistema SHALL controlar ausencias justificadas, injustificadas, medicas e eventos aplicaveis ao eSocial.

#### Scenario: Gestor consulta atestado
- **WHEN** um gestor consulta ausencia com documento medico
- **THEN** o sistema exibe apenas o estado operacional permitido e oculta diagnostico e conteudo clinico

#### Scenario: Documento fora da finalidade
- **WHEN** a finalidade de conservacao de um documento termina e nao existe bloqueio legal
- **THEN** o sistema encaminha o documento para eliminacao ou revisao conforme a politica, preservando auditoria

**8. Avaliação, Desenvolvimento e Reconhecimento**

### Requirement: Avaliacao justa e nao discriminatoria
O sistema SHALL informar previamente criterios de avaliacao, impedir criterios discriminatorios, restringir avaliações privadas, aceitar apenas reconhecimento positivo no espaco publico, permitir contestacao ou revisao humana e impedir que decisoes automaticas promovam, punam ou desliguem pessoas. O sistema SHALL evitar rankings, recomendacoes ou restricoes baseados em raça, etnia, sexo, gravidez, idade, deficiencia, religiao, orientacao sexual, saude, filiação sindical ou opiniao politica.

#### Scenario: Criterio discriminatorio
- **WHEN** um administrador tenta usar atributo protegido em ranking ou recomendacao
- **THEN** o sistema rejeita a configuracao e registra o bloqueio

#### Scenario: Avaliacao contestada
- **WHEN** um colaborador contesta uma avaliacao concluida
- **THEN** o sistema abre revisao humana sem alterar retroativamente a avaliacao original

### Requirement: Avaliacoes, feedbacks, metas e PDI
O sistema SHALL suportar ciclos de avaliacao, competencias, respostas, metas anuais, progresso, conclusao e PDI. O ciclo de avaliacao SHALL seguir somente as transicoes `planejamento` → `em_andamento` → `fechamento` → `concluido`, alem de `cancelado` a partir de qualquer estado nao final, alteradas por RH ou Admin. Metas e avaliacoes SHALL ser criadas somente em ciclo `em_andamento`. Feedback entre gestor e colaborador SHALL ser privado; feedback entre colaboradores SHALL ser publico, sujeito a moderacao e visivel conforme o tipo definido.

#### Scenario: Meta acompanhada
- **WHEN** um colaborador cria uma meta em ciclo ativo e atualiza seu progresso
- **THEN** o sistema registra indicador, valor esperado, prazo, percentual, comentarios e resultado final

#### Scenario: Transicao invalida de ciclo
- **WHEN** RH tenta mudar um ciclo de `planejamento` direto para `concluido`, ou alterar um ciclo `concluido` ou `cancelado`
- **THEN** o sistema rejeita a transicao e mantem o status atual

#### Scenario: Meta em ciclo fora de andamento
- **WHEN** alguem tenta criar meta ou avaliacao vinculada a ciclo que nao esta `em_andamento`
- **THEN** o sistema rejeita a criacao

#### Scenario: Feedback privado
- **WHEN** um gestor envia feedback ao colaborador avaliado
- **THEN** somente participantes autorizados e RH conforme permissao conseguem consultar o conteudo

#### Scenario: Feedback publico
- **WHEN** um colaborador envia reconhecimento ou feedback a outro colaborador
- **THEN** o sistema publica o conteudo conforme regras de visibilidade e permite moderacao registrada

### Requirement: Desenvolvimento e reconhecimento
O sistema SHALL registrar reunioes individuais, check-ins e historico de metas, reconhecimento publico exclusivamente positivo, feedback corretivo privado, pesquisas anonimas de clima com resultados agrupados, matriz de competencias e plano de carreira sem promocao automatica. A pesquisa de clima SHALL armazenar as respostas de forma que nao seja possivel associar uma resposta a um colaborador, nem cruzando a participacao com as respostas por data, horario ou ordem de gravacao. O sistema SHALL aceitar respostas somente de pesquisa ativa, dentro do periodo entre `data_inicio` e `data_fim`, de colaborador nao desligado com usuario ativo e senha ja trocada. RH ou Admin SHALL poder encerrar uma pesquisa, que deixa de aceitar respostas.

#### Scenario: Check-in de meta
- **WHEN** colaborador ou gestor registra um check-in
- **THEN** o sistema preserva progresso, comentarios, dificuldades, evidencias, alteracoes de prazo e historico

#### Scenario: Reconhecimento moderado
- **WHEN** um colaborador envia reconhecimento a outro
- **THEN** o sistema aceita somente conteudo positivo, associa competencia, aplica moderacao e controla visibilidade

#### Scenario: Pesquisa com poucas respostas
- **WHEN** um grupo possui respostas abaixo da quantidade minima configurada
- **THEN** o sistema nao exibe o resultado individual ou agrupado daquele grupo

#### Scenario: Anonimato da resposta
- **WHEN** alguem com acesso as tabelas cruza os registros de participacao com os registros de resposta
- **THEN** nao e possivel determinar a nota dada por nenhum colaborador especifico

#### Scenario: Resposta fora do periodo ou de pesquisa encerrada
- **WHEN** um colaborador tenta responder uma pesquisa inativa, encerrada, antes de `data_inicio` ou depois de `data_fim`
- **THEN** o sistema recusa a resposta sem registrar participacao

#### Scenario: Plano de carreira consultado
- **WHEN** o colaborador consulta sua carreira
- **THEN** o sistema exibe nivel atual, proximo nivel, competencias, lacunas, metas, PDI e evolucao sem promover automaticamente

### Requirement: Onboarding de colaborador
O sistema SHALL oferecer checklist de admissao com dados pessoais, acesso, troca de senha, documentos obrigatorios, aprovacoes, gestor, departamento, contrato, jornada, metas iniciais e acompanhamentos de 30, 60 e 90 dias. Quando todos os itens estiverem concluidos, o onboarding SHALL passar para `concluido` automaticamente.

#### Scenario: Onboarding acompanhado
- **WHEN** RH inicia o onboarding de um colaborador
- **THEN** o sistema cria o checklist, calcula o progresso e aponta os itens pendentes por responsavel

#### Scenario: Item de onboarding concluido
- **WHEN** uma etapa e concluida por usuario autorizado
- **THEN** o sistema registra data, responsavel e evidencia sem permitir conclusao indevida fora do fluxo

#### Scenario: Ultimo item concluido
- **WHEN** o ultimo item pendente do checklist e concluido
- **THEN** o sistema marca o onboarding como `concluido`

### Requirement: Central de tarefas e pendencias
O sistema SHALL apresentar uma central personalizada por perfil com documentos aguardando envio ou analise, ferias e correcoes de ponto pendentes, avaliacoes nao respondidas, metas e PDIs atrasados, pendencia de senha temporaria, cadastro incompleto e jornadas do dia sem marcacao de saida.

#### Scenario: Central do colaborador
- **WHEN** um colaborador acessa sua central
- **THEN** o sistema exibe somente suas pendencias e as acoes autorizadas para resolve-las

#### Scenario: Central do gestor ou RH
- **WHEN** um gestor ou RH acessa sua central
- **THEN** o sistema exibe pendencias sob seu escopo e tarefas de aprovacao ou analise correspondentes

#### Scenario: Dashboard do gestor
- **WHEN** um Gestor acessa seu dashboard
- **THEN** o sistema exibe tamanho da equipe, ausencias, ferias proximas, avaliacoes pendentes e situacao do ponto do dia, restritos aos colaboradores da sua equipe

### Requirement: Central de solicitacoes do colaborador
O sistema SHALL permitir que o colaborador registre solicitacoes ao RH dos tipos `alteracao_cadastral`, `declaracao`, `documento_avulso` ou `outra`, com descricao, campo/valor pretendido quando aplicavel, e acompanhe o status `recebida`, `em_analise`, `atendida` ou `indeferida`. RH SHALL poder analisar, responder e decidir cada solicitacao, registrando justificativa. Uma solicitacao de `alteracao_cadastral` aprovada SHALL exigir que RH aplique a mudanca pelo fluxo de cadastro existente, preservando o historico profissional; a aprovacao da solicitacao nao altera o cadastro automaticamente. O sistema SHALL exibir nessa mesma central, para consulta do colaborador, o status das suas solicitacoes de ferias, ausencia e correcao de ponto, sem duplicar os fluxos ja existentes para esses tipos.

#### Scenario: Solicitacao registrada
- **WHEN** um colaborador cria uma solicitacao com tipo e descricao
- **THEN** o sistema registra a solicitacao como `recebida` e notifica o RH

#### Scenario: Decisao da solicitacao
- **WHEN** RH analisa e decide uma solicitacao, atendendo ou indeferindo
- **THEN** o sistema registra responsavel, justificativa e notifica o colaborador

#### Scenario: Alteracao cadastral nao automatica
- **WHEN** uma solicitacao de `alteracao_cadastral` e aprovada
- **THEN** o sistema nao altera o cadastro sozinho; a mudanca exige que RH a aplique pelo fluxo de cadastro existente, preservando o historico

#### Scenario: Central unificada
- **WHEN** o colaborador acessa a central de solicitacoes
- **THEN** o sistema exibe suas proprias solicitacoes de todos os tipos, incluindo ferias, ausencia e correcao de ponto, com o status atual de cada uma

### Requirement: Comunicados internos
O sistema SHALL permitir que RH ou Admin publiquem comunicados internos com titulo, conteudo, publico-alvo (todos, departamento ou perfil especifico) e vigencia. O sistema SHALL exibir no dashboard dos colaboradores somente os comunicados vigentes dentro do publico-alvo definido.

#### Scenario: Comunicado publicado
- **WHEN** RH publica um comunicado com publico-alvo definido
- **THEN** o sistema o exibe apenas aos colaboradores dentro desse publico

#### Scenario: Comunicado expirado
- **WHEN** a vigencia de um comunicado termina
- **THEN** o sistema deixa de exibi-lo no dashboard sem apagar o registro

### Requirement: Base de conhecimento do RH
O sistema SHALL manter artigos de FAQ organizados por categoria (ferias, ponto, documentos, politicas internas), mantidos por RH ou Admin, e disponiveis para consulta por todos os colaboradores autenticados. Conteudo sobre beneficios fica fora do escopo desta mudanca.

#### Scenario: Consulta de FAQ
- **WHEN** um colaborador busca ou navega pela base de conhecimento
- **THEN** o sistema exibe os artigos publicados, organizados por categoria

**10. Auditoria, Notificações e Segurança Operacional**

### Requirement: Auditoria obrigatoria
O sistema SHALL auditar autenticacao, logout, troca e redefinicao de senha, codigo de acesso de login, usuarios, alteracoes contratuais, dados bancarios, ponto e ajustes, decisoes, documentos, regras trabalhistas, exportacoes e alteracoes em avaliacoes concluidas, incluindo responsavel, data, justificativa e valores anterior e novo. O sistema SHALL negar por padrao, preservar historicos e nunca apagar evidencias silenciosamente.

#### Scenario: Operacao sensivel auditada
- **WHEN** ocorre uma alteracao de regra, documento, contrato, ponto ou avaliacao
- **THEN** o sistema cria evento com autor, contexto, valores e resultado consultavel por Admin ou RH

#### Scenario: Tentativa sem permissao
- **WHEN** um usuario tenta operar fora do seu escopo
- **THEN** o sistema nega por padrao e registra a tentativa conforme a politica

### Requirement: Auditoria e notificacoes
O sistema SHALL registrar eventos sensiveis, incluindo autenticacao, alteracoes cadastrais, decisoes, acessos a documentos e moderacao. Notificacoes de pendencias, decisoes e eventos de prazo SHALL ser entregues por e-mail sem expor dados sensiveis no assunto ou em links sem protecao. Cada evento notificavel SHALL tambem gerar uma notificacao interna vinculada ao usuario, marcavel como lida, alem do envio por e-mail.

#### Scenario: Decisao rastreavel
- **WHEN** uma solicitacao de ponto, ferias ou ausencia e aprovada, recusada ou cancelada
- **THEN** o sistema registra autor, data, acao, justificativa e estado anterior e posterior

#### Scenario: Falha no envio de e-mail
- **WHEN** o provedor de e-mail nao aceita uma notificacao
- **THEN** o sistema preserva a pendencia, registra a falha e permite reprocessamento sem duplicar a decisao

#### Scenario: Notificacao interna consultada
- **WHEN** um evento gera notificacao, como ferias aprovada, documento vencendo, avaliacao disponivel ou solicitacao respondida
- **THEN** o sistema registra uma notificacao interna vinculada ao usuario, alem do envio por e-mail

### Requirement: Auditoria consultavel
O sistema SHALL permitir que Admin e RH consultem autor, acao, registro afetado, valor anterior, valor novo, data, horario, IP ou sessao, justificativa e resultado da operacao.

#### Scenario: Consulta de auditoria
- **WHEN** Admin ou RH filtra eventos auditados
- **THEN** o sistema retorna os detalhes permitidos e respeita filtros de periodo, usuario, recurso e resultado

#### Scenario: Auditoria restrita
- **WHEN** um Colaborador ou Gestor tenta consultar o painel administrativo
- **THEN** o sistema nega o acesso e registra a tentativa conforme a politica de seguranca

### Requirement: API, rastreamento e operacao
O sistema SHALL versionar a API pelo grupo de API do Xano, cuja URL base identifica a versao publicada; o prefixo `/api/v1/` nao e exigido. A geracao de identificador de rastreamento por requisicao e sua correlacao com logs, auditoria, e-mail e erros ficam fora do MVP e registradas no backlog. O sistema SHALL monitorar erros de API, rotinas manuais, e-mails, documentos, filas e tentativas bloqueadas e SHALL possuir procedimento de backup e restauracao documentado e testado ao menos uma vez.

#### Scenario: Requisicao rastreavel
- **WHEN** uma operacao gera evento de auditoria e mensagem de e-mail
- **THEN** a correlacao e feita pelo usuario, recurso, registro e horario gravados na auditoria e pela chave de idempotencia do `email_outbox`; o identificador unico por requisicao fica no backlog

#### Scenario: Falha operacional detectada
- **WHEN** uma rotina manual tem itens pendentes ou uma fila acumula itens acima do limite
- **THEN** o sistema disponibiliza o indicador operacional correspondente e permite diagnostico

#### Scenario: Restauracao testada
- **WHEN** o procedimento de backup documentado e executado e restaurado em um workspace de teste
- **THEN** o schema e os dados restaurados correspondem ao backup, e o resultado fica registrado nas evidencias do projeto

### Requirement: Indicadores, exportacoes e preferencias
O sistema SHALL disponibilizar indicadores de colaboradores, contratos, ponto, ausencias, ferias, documentos, avaliacoes, metas, PDIs e aprovacoes, incluindo headcount, turnover, admissoes, desligamentos, absenteismo, distribuicao por departamento e horas extras. O sistema SHALL exportar CSV ou PDF respeitando permissoes e registrar a exportacao. O sistema SHALL permitir preferencias de canal e frequencia, sem desativar alertas obrigatorios de seguranca.

#### Scenario: Exportacao autorizada
- **WHEN** um usuario autorizado exporta um relatorio
- **THEN** o arquivo inclui somente dados do seu escopo e a exportacao e auditada

### Requirement: Acessibilidade e validacao de CPF
O frontend SHALL oferecer navegacao por teclado, contraste adequado, labels, foco visivel, mensagens compreensiveis, responsividade, textos alternativos e status que nao dependam somente de cor. O sistema SHALL validar CPF exclusivamente pelo algoritmo local, sem API externa.

#### Scenario: CPF valido
- **WHEN** um CPF e submetido ao cadastro
- **THEN** o sistema aceita o cadastro quando a validacao local for positiva

#### Scenario: CPF invalido ou servico indisponivel
- **WHEN** a validacao local for negativa
- **THEN** o sistema impede a conclusao do cadastro e informa o campo invalido sem expor dados sensiveis

### Requirement: Cobertura das telas do protótipo Figma
O frontend SHALL implementar uma tela ou fluxo correspondente para cada tela navegável definida no protótipo Figma "ConectaRH — Protótipo" (`fph1M5tB4rA4gqfIysSmkn`), cobrindo o conteúdo e a hierarquia de informação documentados ali para cada rota.

#### Scenario: Login e código de acesso
- **WHEN** um usuário acessa o app sem sessão ativa
- **THEN** o sistema apresenta a tela de login (e-mail/senha) e, após senha válida, a tela de código de acesso (OTP de 6 dígitos), na sequência definida no protótipo

#### Scenario: Início
- **WHEN** um usuário autenticado acessa o app
- **THEN** o sistema apresenta uma tela de início/dashboard com saudação e atalhos principais

#### Scenario: Central de pendências
- **WHEN** um usuário autenticado navega para a central de pendências
- **THEN** o sistema apresenta a fila de aprovação aplicável ao perfil do usuário (RH/ADMIN vê todas; Gestor vê só o próprio departamento; Colaborador não vê a fila administrativa)

#### Scenario: Perfil
- **WHEN** um usuário autenticado navega para o próprio perfil
- **THEN** o sistema apresenta os dados pessoais e, quando aplicável, a edição dos próprios dados bancários

#### Scenario: Pagamento
- **WHEN** um colaborador navega para a área de pagamento
- **THEN** o sistema apresenta os documentos do tipo holerite/informe de rendimentos anexados pelo RH, disponíveis para consulta e download

#### Scenario: Onboarding
- **WHEN** um usuário autenticado com onboarding em andamento acessa a tela de onboarding
- **THEN** o sistema apresenta o checklist por categoria com responsável e percentual concluído

#### Scenario: Ponto
- **WHEN** um colaborador acessa a tela de ponto
- **THEN** o sistema apresenta a marcação do dia, o espelho de ponto e a opção de solicitar correção, incluindo o aviso de que o registro é controle interno experimental

#### Scenario: Férias
- **WHEN** um usuário autenticado acessa a tela de férias/ausências
- **THEN** o sistema apresenta a solicitação de férias/ausência e, para RH/ADMIN, a fila de decisão

#### Scenario: Documentos
- **WHEN** um usuário autenticado acessa a tela de documentos
- **THEN** o sistema apresenta o envio e a listagem de documentos por status, incluindo pendências abertas

#### Scenario: Auditoria
- **WHEN** um usuário com perfil RH ou ADMIN acessa a tela de auditoria
- **THEN** o sistema apresenta a consulta à trilha de auditoria com os filtros disponíveis; um usuário com outro perfil não vê essa tela

#### Scenario: Regras
- **WHEN** um usuário com perfil RH ou ADMIN acessa a tela de regras
- **THEN** o sistema apresenta a gestão de instrumentos normativos e regras de override, incluindo a simulação de impacto antes de publicar

#### Scenario: Trajetória
- **WHEN** um usuário autenticado acessa a tela de trajetória
- **THEN** o sistema apresenta avaliação, metas, PDI e o painel de plano de carreira (nível atual, próximo nível, lacunas), sem nenhuma ação de promoção automática

### Requirement: Fidelidade ao design system do Figma
O frontend SHALL aplicar os tokens de cor e tipografia definidos na página "Design System" do protótipo Figma (paleta grafite `#16181D` + âmbar `#F5A623` como acento único; tipografia Sora para títulos e Manrope para texto corrente) de forma consistente em todas as telas, e SHALL reutilizar os componentes de assinatura do protótipo ("crachá de acesso", "trilha de conexão") onde o protótipo os emprega, em vez de criar um padrão visual alternativo por tela.

#### Scenario: Divergência de cor ou tipografia
- **WHEN** uma tela implementada usa uma cor ou fonte fora dos tokens do design system
- **THEN** isso é tratado como um defeito da implementação, não como uma variação aceitável

### Requirement: Estados de UI obrigatórios
Cada tela do frontend SHALL tratar explicitamente os 6 estados exigidos pelo design system do protótipo: carregando, vazio, sucesso, erro, bloqueado e permissão negada.

#### Scenario: Requisição em andamento
- **WHEN** uma tela está aguardando resposta de um endpoint do backend
- **THEN** o sistema comunica visualmente o estado de carregamento em vez de apresentar uma tela em branco ou travada

#### Scenario: Ausência de dados
- **WHEN** uma listagem não tem nenhum item para exibir
- **THEN** o sistema apresenta um estado vazio explicativo, não uma tabela ou lista em branco sem contexto

#### Scenario: Erro do backend
- **WHEN** uma chamada ao backend retorna erro
- **THEN** o sistema apresenta a mensagem de erro retornada pela API de forma compreensível, sem expor detalhes técnicos internos (stack trace, payload bruto)

#### Scenario: Acesso negado por perfil
- **WHEN** um usuário autenticado sem o perfil necessário tenta acessar uma tela restrita
- **THEN** o sistema apresenta um estado de permissão negada em vez de tentar renderizar a tela com dados incompletos

### Requirement: Validação dos campos antes do envio
O frontend SHALL validar e normalizar cada campo de entrada antes de chamar o backend, aplicando as mesmas regras que o backend já aplica, e SHALL recusar no próprio cliente, com mensagem em português, toda entrada que o backend com certeza recusaria. Na tela "Entrar" as regras são:
- e-mail: espaços nas pontas removidos, letras minúsculas, até 254 caracteres, só ASCII e formato `nome@dominio.tld`;
- senha do login: de 8 a 64 caracteres e não pode ser só espaços;
- código de acesso e código de redefinição: exatamente 6 dígitos numéricos;
- nova senha: de 8 a 64 caracteres e igual à confirmação.

A validação no cliente é só conveniência: o backend continua validando e recusando as mesmas entradas, conforme o requisito "Frontend não decide autorização".

#### Scenario: E-mail com emoji, acento ou caractere especial
- **WHEN** o usuário informa um e-mail com emoji (ex.: `teste😀@empresa.com`) ou acento (ex.: `joão@empresa.com`)
- **THEN** o sistema não envia a requisição e informa que o e-mail não pode ter acentos, emojis ou outros caracteres especiais

#### Scenario: E-mail fora do formato
- **WHEN** o usuário informa um e-mail sem `@`, com HTML/script (ex.: `<script>alert(1)</script>`) ou com SQL (ex.: `' OR '1'='1`)
- **THEN** o sistema não envia a requisição e pede um e-mail no formato `nome@empresa.com`

#### Scenario: Campo só com espaços
- **WHEN** o usuário preenche e-mail, senha, código ou nova senha só com espaços
- **THEN** o sistema trata o campo como vazio e pede o preenchimento, sem enviar a requisição

#### Scenario: E-mail com espaços nas pontas ou maiúsculas
- **WHEN** o usuário informa um e-mail válido com espaços nas pontas ou letras maiúsculas
- **THEN** o sistema remove os espaços, converte para minúsculas, envia o e-mail normalizado e o exibe assim nas etapas seguintes

#### Scenario: Senha fora do tamanho
- **WHEN** a senha do login tem menos de 8 caracteres (ex.: só 3 emojis)
- **THEN** o sistema informa que a senha tem entre 8 e 64 caracteres e não envia a tentativa, que contaria para o bloqueio por senha errada

#### Scenario: Texto acima do limite do campo
- **WHEN** o usuário cola num campo um texto maior que o limite (254 para e-mail, 64 para senha, 6 para código)
- **THEN** o campo não aceita o conteúdo colado e, ao enviar, o sistema informa que o campo está vazio

#### Scenario: Código de acesso sem formato
- **WHEN** o usuário digita um código com letras, emoji, espaço, HTML ou menos de 6 dígitos
- **THEN** o sistema informa que o código tem exatamente 6 números e não envia a requisição, preservando as 5 tentativas de validação do código

#### Scenario: Confirmação de senha diferente
- **WHEN** a nova senha e a confirmação não coincidem
- **THEN** o sistema informa que a confirmação não corresponde à nova senha, sem enviar a requisição

#### Scenario: Mensagem técnica do backend
- **WHEN** o backend recusa uma entrada com mensagem técnica em inglês (ex.: `Invalid email format.`, `Missing param: ...`, `Input does not meet minimum length requirement of 8 characters`)
- **THEN** o sistema exibe a mensagem equivalente em português

#### Scenario: Falha de conexão com o servidor
- **WHEN** a chamada ao backend falha por rede, TLS ou tempo esgotado
- **THEN** o sistema exibe uma mensagem amigável pedindo para tentar de novo, e o detalhe técnico vai só para o log do servidor

#### Scenario: Reenviar o código de redefinição
- **WHEN** o usuário está na tela de redefinir senha e pede "Reenviar código"
- **THEN** o sistema envia um novo código, que substitui o anterior, só se tiver passado pelo menos 60 segundos desde o último envio; antes disso, pede para aguardar, e o backend também ignora o pedido, sem enviar e-mail

#### Scenario: Senha redefinida com sucesso
- **WHEN** o usuário redefine a senha com um código válido
- **THEN** o sistema volta para a tela de login exibindo a confirmação de sucesso, e o login com a nova senha funciona mesmo que a conta estivesse bloqueada por senhas erradas

#### Scenario: Dado digitado exibido na tela
- **WHEN** a tela exibe um valor informado pelo usuário (ex.: o e-mail no passo do código de acesso)
- **THEN** o valor é exibido como texto escapado, sem ser interpretado como HTML

### Requirement: Acessibilidade
O frontend SHALL seguir os critérios de acessibilidade documentados na página "Design System" do protótipo: contraste mínimo WCAG AA entre texto e fundo, foco visível em todo elemento navegável por teclado, navegação completa por teclado nos fluxos principais, e nenhuma informação transmitida exclusivamente por cor.

#### Scenario: Navegação por teclado
- **WHEN** um usuário navega o formulário de login usando somente o teclado
- **THEN** todos os campos e botões são alcançáveis em ordem lógica, com indicação visual clara de qual elemento está focado

#### Scenario: Informação de estado sem depender só de cor
- **WHEN** o sistema indica o status de um item (ex.: pendente/aprovado/rejeitado)
- **THEN** o status é indicado por texto ou ícone além da cor, para permanecer compreensível a usuários com daltonismo

### Requirement: Frontend não decide autorização
O frontend SHALL tratar toda decisão de autorização (o que um perfil pode ver ou fazer) como resultado vindo do backend, nunca como lógica decidida ou replicada no cliente — consistente com a arquitetura já estabelecida em `AGENTS.md`.

#### Scenario: Ocultação de tela restrita
- **WHEN** o app decide esconder ou desabilitar uma ação restrita a determinado perfil
- **THEN** essa decisão reflete o perfil e os dados retornados pelo backend na sessão autenticada, e o backend também rejeita a mesma ação caso seja tentada diretamente pela API

### Requirement: Guarda de acesso em todo endpoint autenticado
Todo endpoint autenticado SHALL recarregar o usuário do token e recusar a requisição quando o usuário não existir, estiver inativo, possuir senha temporária pendente de troca ou quando a sessão vinculada ao token estiver encerrada, revogada ou expirada. A recusa por senha temporária SHALL ter como únicas exceções a troca de senha, a consulta do próprio usuário (`auth/me`), o logout e as rotas de consulta e encerramento de sessões.

#### Scenario: Usuário com senha temporária chama endpoint de negócio
- **WHEN** um usuário com senha temporária pendente chama qualquer endpoint autenticado fora das exceções
- **THEN** o sistema nega o acesso e informa que a senha temporária precisa ser trocada

#### Scenario: Usuário com senha temporária troca a senha
- **WHEN** um usuário com senha temporária pendente chama a troca de senha com o token recebido no login
- **THEN** o sistema aceita a troca e, a partir daí, libera os demais endpoints conforme o perfil

#### Scenario: Usuário desativado com token ainda válido
- **WHEN** um usuário é desativado e depois usa um token emitido antes da desativação
- **THEN** o sistema nega a requisição em qualquer endpoint autenticado

#### Scenario: Token de sessão encerrada
- **WHEN** uma requisição usa um token cuja sessão foi encerrada por logout, por encerramento seletivo ou por revogação
- **THEN** o sistema nega a requisição, mesmo que o token ainda não tenha expirado

### Requirement: Bloqueio de autoaprovação em decisões
O sistema SHALL impedir que um usuário decida (aprovar, rejeitar, registrar, atender, indeferir, revisar, iniciar análise ou concluir) uma solicitação cujo colaborador seja ele mesmo, em férias, ausências, correções de ponto, documentos, desligamentos, solicitações ao RH e contestações de avaliação, para qualquer perfil, incluindo RH e Admin. A tentativa bloqueada SHALL gerar evento de auditoria com resultado de falha.

#### Scenario: RH tenta aprovar as próprias férias
- **WHEN** um usuário RH tenta aprovar uma solicitação de férias em que ele é o colaborador
- **THEN** o sistema nega a decisão, mantém a solicitação no status anterior e registra a tentativa na auditoria

#### Scenario: Gestor tenta aprovar a própria correção de ponto
- **WHEN** um Gestor tenta aprovar uma correção de ponto do seu próprio registro
- **THEN** o sistema nega a decisão e registra a tentativa na auditoria

#### Scenario: Decisão sobre solicitação de outra pessoa
- **WHEN** um decisor autorizado decide uma solicitação de outro colaborador dentro do seu escopo
- **THEN** o sistema aplica a decisão normalmente

### Requirement: Transições de status por rotina acionada manualmente
O sistema SHALL oferecer a RH e Admin uma rotina diária de acionamento manual que aplica as transições de status dependentes de data. Ela SHALL: mudar férias `Aprovada` com data final no passado para `Concluida`; colocar como `Ferias` o colaborador com férias aprovadas em andamento e voltar para `Ativo` ao final; colocar como `Afastado` o colaborador com afastamento aprovado em andamento e voltar para `Ativo` ao final; mudar para `Incompleto` o registro de ponto `Aberto` de dias anteriores; mudar para `expirado` o instrumento normativo `vigente` com vigência encerrada; e concluir os desligamentos agendados cuja data efetiva já chegou. A rotina SHALL ser idempotente, nunca reativar colaborador `Desligado` e registrar na auditoria um evento com a contagem de cada transição aplicada.

#### Scenario: Rotina executada duas vezes no mesmo dia
- **WHEN** RH aciona a rotina e logo depois aciona de novo
- **THEN** a segunda execução não aplica nenhuma transição repetida e informa contagens zeradas

#### Scenario: Férias encerradas
- **WHEN** a rotina encontra férias `Aprovada` com data final anterior a hoje
- **THEN** muda as férias para `Concluida` e devolve o colaborador ao status `Ativo` se ele estava como `Ferias` e não tiver outro afastamento vigente

#### Scenario: Colaborador desligado não é reativado
- **WHEN** a rotina encontra férias ou afastamento terminado de um colaborador `Desligado`
- **THEN** o status do colaborador permanece `Desligado`

#### Scenario: Perfil sem permissão
- **WHEN** um Gestor ou Colaborador tenta acionar a rotina
- **THEN** o sistema nega o acesso

### Requirement: Visão da equipe do gestor
O sistema SHALL oferecer ao Gestor uma consulta da própria equipe, restrita aos colaboradores do departamento que ele gerencia, com nome, cargo, status, férias aprovadas próximas, ausências aprovadas vigentes ou próximas (só tipo, período e status) e situação do ponto do dia. A consulta não SHALL retornar CPF, salário, dados bancários, contato pessoal, conteúdo de atestado ou diagnóstico. A consulta individual completa de colaborador continua restrita a RH e Admin.

#### Scenario: Gestor consulta a equipe
- **WHEN** um Gestor consulta sua equipe
- **THEN** o sistema retorna somente os colaboradores do departamento que ele gerencia, sem campos sensíveis

#### Scenario: Usuário que não é Gestor
- **WHEN** um Colaborador, RH ou Admin chama a consulta de equipe
- **THEN** o sistema nega o acesso

### Requirement: Alteração de e-mail de conta notificada ao titular
Quando RH ou Admin alterar o e-mail de acesso de uma conta, o sistema SHALL enviar um alerta para o e-mail anterior informando a alteração, sem incluir o novo endereço completo, e SHALL registrar a alteração na auditoria com autor e valores anterior e novo.

#### Scenario: RH altera o e-mail de um colaborador
- **WHEN** RH altera o e-mail de acesso de uma conta
- **THEN** o sistema grava a alteração, enfileira um alerta para o e-mail anterior e cria o evento de auditoria

### Requirement: Protótipo Figma como fonte única do frontend
O frontend Streamlit SHALL ser construído exclusivamente a partir do protótipo oficial no Figma (`https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn/ConectaRH-%E2%80%94-Prot%C3%B3tipo?node-id=0-1&t=Gk8mcdzJ1dE1KMP7-1`). Cores, tipografia, espaçamentos, ícones, componentes, textos e rótulos de cada tela SHALL corresponder ao nó da tela no protótipo e aos tokens do design system. Uma tela ou estado de UI que não exista no protótipo não SHALL ser implementado antes de ser desenhado no Figma seguindo o design system. Cada entrega de tela SHALL indicar o nó do Figma usado como referência e apresentar a comparação visual entre a tela pronta e o nó.

#### Scenario: Tela sem nó no protótipo
- **WHEN** uma tela ou estado de UI necessário não existe no protótipo
- **THEN** a pendência é registrada e a tela é desenhada no Figma antes de qualquer implementação no Streamlit

#### Scenario: Elemento visual fora do protótipo
- **WHEN** uma tela implementada usa layout, cor, fonte, componente ou texto que não existe no nó correspondente do protótipo
- **THEN** isso é tratado como defeito e corrigido para ficar igual ao protótipo

#### Scenario: Entrega de tela
- **WHEN** uma tela é entregue para revisão
- **THEN** a entrega inclui o link do nó do Figma e a comparação visual entre a tela implementada e o protótipo

### Requirement: Transparência sobre o tratamento de dados
O sistema SHALL disponibilizar ao colaborador um aviso de privacidade em linguagem simples, acessível sem login a partir da tela Entrar e, depois do login, na tela "Privacidade". O aviso SHALL informar:
- quais dados são coletados e com qual finalidade;
- a base legal de cada finalidade;
- com quais operadores os dados são compartilhados;
- por quanto tempo os dados são guardados;
- que IP e dispositivo são registrados no login e na auditoria;
- quais são os direitos do titular e como exercê-los;
- o contato do encarregado.

O aviso SHALL cobrir todas as finalidades do registro de operações de tratamento do projeto (LGPD, arts. 6º, VI, 9º e 41).

#### Scenario: Aviso acessível antes do login
- **WHEN** uma pessoa abre a tela Entrar sem estar autenticada
- **THEN** o sistema exibe um link para o aviso de privacidade, que pode ser lido sem login

#### Scenario: Contato do encarregado
- **WHEN** o colaborador consulta o aviso de privacidade ou a tela "Privacidade"
- **THEN** o sistema exibe o nome e o e-mail de contato do encarregado

#### Scenario: Nova finalidade sem aviso
- **WHEN** o registro de operações ganha uma finalidade que o aviso de privacidade não menciona
- **THEN** isso é tratado como defeito, e a mudança só é integrada depois que o aviso for atualizado

### Requirement: Acesso e portabilidade dos próprios dados
O sistema SHALL permitir que o colaborador autenticado baixe, em JSON e em CSV, todos os dados pessoais que o sistema guarda sobre ele:
- cadastro, contrato e histórico;
- metadados de documentos;
- férias, ausências, ponto e banco de horas;
- avaliações, metas e PDI;
- solicitações e notificações;
- sessões.

A exportação SHALL conter somente dados do próprio titular. Ela SHALL excluir dados de outras pessoas e as respostas de clima, que são anônimas, e SHALL ser auditada (LGPD, art. 18, II e V).

#### Scenario: Colaborador baixa os próprios dados
- **WHEN** o colaborador pede "Baixar meus dados" e escolhe JSON ou CSV
- **THEN** o sistema devolve um arquivo com todas as categorias do inventário que se aplicam a ele e registra o evento `exportar_meus_dados` na auditoria

#### Scenario: Sem dados de terceiros
- **WHEN** o colaborador exporta os próprios dados e é gestor de uma equipe ou foi avaliado por outra pessoa
- **THEN** o arquivo não contém dados pessoais de membros da equipe, de avaliadores ou de qualquer outro colaborador além do necessário para identificar o registro (ex.: nome do avaliador)

#### Scenario: Exportação de outra pessoa
- **WHEN** um usuário tenta exportar os dados de outro colaborador pelo mesmo endpoint
- **THEN** o sistema nega a requisição, qualquer que seja o perfil

### Requirement: Pedidos do titular de dados
O sistema SHALL aceitar na central de solicitações pedidos do tipo `privacidade_lgpd`, com um dos subtipos:
- confirmação de tratamento;
- acesso;
- correção;
- anonimização ou eliminação;
- oposição;
- informação sobre compartilhamento;
- revisão de decisão.

Cada pedido SHALL ter prazo de resposta de 15 dias, visível ao RH e ao solicitante, com alerta na central de tarefas do RH quando faltarem 3 dias ou menos. A resposta e a decisão SHALL ser auditadas e informadas ao colaborador (LGPD, arts. 18 e 19).

#### Scenario: Pedido criado entra na fila do RH
- **WHEN** o colaborador abre um pedido `privacidade_lgpd` com subtipo "acesso"
- **THEN** o pedido aparece na fila do RH com a data-limite de resposta 15 dias após a abertura

#### Scenario: Pedido perto do prazo
- **WHEN** um pedido `privacidade_lgpd` aberto está a 3 dias ou menos da data-limite
- **THEN** a central de tarefas do RH destaca o pedido como próximo do vencimento

#### Scenario: Resposta ao titular
- **WHEN** o RH responde ou decide um pedido `privacidade_lgpd`
- **THEN** o sistema registra autor, data, decisão e justificativa na auditoria e notifica o colaborador

### Requirement: Oposição a tratamentos por legítimo interesse
O sistema SHALL permitir que o colaborador saia da lista de aniversariantes e deixe de aparecer no mural público de reconhecimento. Essas preferências SHALL ser respeitadas por todos os endpoints que expõem esses dados a outros usuários (LGPD, art. 18, § 2º).

#### Scenario: Colaborador sai da lista de aniversariantes
- **WHEN** o colaborador desativa a opção de aparecer entre os aniversariantes
- **THEN** a consulta de aniversariantes deixa de incluí-lo para todos os usuários

#### Scenario: Colaborador sai do mural público
- **WHEN** o colaborador desativa a opção de aparecer no mural de reconhecimento
- **THEN** o mural público deixa de exibir os reconhecimentos dele, que continuam visíveis para ele e para o RH

### Requirement: Minimização e dados sensíveis de saúde
O sistema SHALL tratar como dados sensíveis os atestados, os eventos de saúde e segurança do trabalho (ASO) e os laudos de deficiência. O sistema SHALL NOT coletar raça, sexo, religião, filiação sindical ou biometria.

O motivo de uma ausência SHALL ser escolhido de uma lista fechada (consulta, doença, acompanhamento de familiar e outro), sem texto livre. A observação da ausência SHALL recusar códigos CID, e o atestado SHALL ficar só no arquivo privado. O Gestor SHALL ver somente tipo, período e status da ausência (LGPD, arts. 6º, III, e 11).

#### Scenario: Motivo de ausência escolhido de lista
- **WHEN** o colaborador registra uma ausência
- **THEN** o sistema aceita só um dos motivos da lista fechada e recusa texto livre no campo de motivo

#### Scenario: Diagnóstico na observação
- **WHEN** a observação de uma ausência contém um código CID (ex.: `J11`)
- **THEN** o sistema recusa o registro e orienta a não informar diagnóstico, que fica só no atestado

#### Scenario: Gestor consulta ausência da equipe
- **WHEN** um Gestor consulta ausências da própria equipe por qualquer endpoint
- **THEN** a resposta não contém motivo, observação, comprovante nem documento médico

### Requirement: Acesso a arquivos sensíveis auditado
O sistema SHALL registrar na auditoria cada abertura do arquivo de um documento, de um comprovante de ausência e de um documento de evento de SST, com autor, registro e data, mesmo quando o acesso é permitido.

#### Scenario: RH abre o arquivo de um documento
- **WHEN** um usuário autorizado abre o arquivo de um documento, comprovante de ausência ou documento de SST
- **THEN** o sistema entrega o arquivo e registra o evento `acessar_arquivo_documento` com autor, registro e data

### Requirement: Dados pessoais mascarados na auditoria
A auditoria SHALL registrar os valores anterior e novo de dados pessoais de forma mascarada, sem conta bancária, agência, CPF, salário, telefone, endereço ou e-mail completos. Ainda assim, os valores SHALL ser suficientes para identificar que houve alteração (ex.: `banco=341; agencia=****; conta=****1234`).

#### Scenario: Alteração de dados bancários
- **WHEN** o colaborador altera os próprios dados bancários
- **THEN** a auditoria registra a alteração com agência e conta mascaradas, mostrando no máximo os 4 últimos dígitos da conta

#### Scenario: Nenhum dado completo em auditoria nova
- **WHEN** qualquer endpoint grava auditoria envolvendo CPF, salário, telefone, endereço ou e-mail
- **THEN** o valor gravado está mascarado

### Requirement: Arquivos só em armazenamento controlado
O sistema SHALL aceitar como arquivo de documento ou de evento de SST somente o armazenamento privado do sistema ou domínios aprovados numa lista configurável. O sistema SHALL recusar links públicos de compartilhamento.

#### Scenario: Link público de drive
- **WHEN** um usuário informa como arquivo um link público de compartilhamento de um serviço de nuvem que não está na lista aprovada
- **THEN** o sistema recusa o registro com uma mensagem que explica que só são aceitos arquivos enviados pelo sistema ou de domínios aprovados

### Requirement: Códigos de acesso protegidos
O sistema SHALL guardar os códigos de acesso de login e de redefinição de senha só de forma não reversível, comparando o código digitado com o valor protegido.

#### Scenario: Código não legível no banco
- **WHEN** um código de acesso ou de redefinição é gerado
- **THEN** o banco de dados não contém o código em texto puro, e o login e a redefinição continuam funcionando com o código recebido por e-mail

### Requirement: Indicadores sem identificação de pessoas
Os indicadores e a exportação de indicadores SHALL omitir grupos (ex.: departamentos) com menos pessoas que um mínimo configurável, com padrão de 5. Quando omitir um único grupo permitir deduzir o valor dele pela diferença com o total, o sistema SHALL omitir também o total ou outro grupo.

#### Scenario: Departamento pequeno
- **WHEN** RH consulta ou exporta absenteísmo e afastamentos e um departamento tem 2 pessoas
- **THEN** esse departamento não aparece na consulta nem no CSV exportado

#### Scenario: Dedução pela diferença
- **WHEN** um único departamento é omitido e o total geral seria exibido
- **THEN** o sistema também omite o total ou outro grupo, de modo que o valor do departamento omitido não possa ser calculado

### Requirement: Retenção e anonimização
O sistema SHALL manter um prazo de guarda por categoria de dado e SHALL limpar, na rotina diária acionada pelo RH, as sessões e as mensagens de e-mail enviadas cujo prazo venceu. O sistema SHALL permitir que RH ou Admin anonimizem, com justificativa, um colaborador desligado cujo prazo de guarda terminou:
- nome, CPF, contato, endereço, data de nascimento e dados bancários são substituídos;
- o histórico agregado e a auditoria são preservados, sem os valores pessoais;
- nenhum registro é excluído fisicamente.

A anonimização SHALL ser recusada enquanto houver prazo legal de guarda ou processo em aberto (LGPD, arts. 15, 16 e 18, IV).

#### Scenario: Limpeza de dados vencidos
- **WHEN** RH aciona a rotina diária e existem sessões ou mensagens de e-mail enviadas com prazo de guarda vencido
- **THEN** a rotina remove os dados pessoais desses registros, registra as contagens na auditoria e, se executada de novo, não altera nada

#### Scenario: Anonimização de desligado
- **WHEN** RH anonimiza, com justificativa, um colaborador desligado com prazo de guarda cumprido
- **THEN** nenhum endpoint devolve mais dado que identifique a pessoa, e os indicadores agregados continuam corretos

#### Scenario: Anonimização antes do prazo
- **WHEN** RH tenta anonimizar um colaborador com prazo legal de guarda ainda vigente ou com processo em aberto
- **THEN** o sistema recusa a operação e informa o motivo

### Requirement: Dados de adolescentes
Para colaborador com menos de 18 anos, o sistema SHALL exigir o documento de responsável legal antes de ativar o contrato e SHALL deixá-lo, por padrão, fora da lista de aniversariantes e do mural público de reconhecimento (LGPD, art. 14).

#### Scenario: Aprendiz sem responsável legal
- **WHEN** RH tenta ativar o contrato de um aprendiz de 16 anos sem documento de responsável legal
- **THEN** o sistema bloqueia a ativação e informa o documento que falta

#### Scenario: Aprendiz fora da exposição pública
- **WHEN** um colaborador de 16 anos é cadastrado
- **THEN** ele não aparece entre os aniversariantes nem no mural público até que a preferência seja alterada

### Requirement: Resposta a incidentes de segurança
O projeto SHALL manter um plano de resposta a incidentes com dados pessoais. O plano SHALL definir:
- quem detecta e quem avalia o incidente;
- os critérios de risco;
- o modelo de comunicação à ANPD e aos titulares em até 3 dias úteis;
- o registro interno de todo incidente, inclusive os não comunicados (LGPD, art. 48; Resolução CD/ANPD nº 15/2024).

#### Scenario: Incidente simulado
- **WHEN** a equipe simula um incidente, como um token de acesso vazado
- **THEN** o incidente percorre o plano do começo ao fim e fica registrado internamente, sem dados pessoais no registro

### Requirement: Operadores e transferência internacional
O projeto SHALL manter a lista de todos os serviços externos que recebem dados pessoais. Para cada um, a lista SHALL registrar:
- quais dados o serviço recebe;
- a região onde os dados ficam;
- os termos de tratamento de dados do fornecedor;
- o mecanismo de transferência internacional.

Um novo serviço externo SHALL entrar nessa lista antes de receber dados (LGPD, arts. 33 a 39; Resolução CD/ANPD nº 19/2024).

#### Scenario: Novo serviço externo
- **WHEN** o código passa a enviar dados pessoais para um serviço que não está na lista de operadores
- **THEN** isso é tratado como defeito, e a mudança só é integrada depois que a lista e o registro de operações forem atualizados
