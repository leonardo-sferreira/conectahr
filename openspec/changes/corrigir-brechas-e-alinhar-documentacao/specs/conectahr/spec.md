## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Organograma da empresa
O sistema SHALL apresentar uma visualizacao hierarquica da estrutura organizacional, reunindo departamentos, gestores e colaboradores vinculados, a partir dos dados ja mantidos de cargo, departamento e vinculo gestor-colaborador. O organograma SHALL incluir todo colaborador cujo status nao seja `Desligado`, inclusive quem estiver de ferias ou afastado. O sistema SHALL restringir a visualizacao a nome, cargo e departamento de cada pessoa, sem expor dados sensiveis.

#### Scenario: Consulta do organograma
- **WHEN** um usuario autenticado acessa o organograma
- **THEN** o sistema exibe departamentos, gestores e colaboradores em estrutura hierarquica, mostrando apenas nome, cargo e departamento de cada pessoa

#### Scenario: Colaborador de ferias no organograma
- **WHEN** um colaborador esta com status `Ferias` ou `Afastado`
- **THEN** ele continua aparecendo no organograma; somente colaboradores `Desligado` sao omitidos

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

### Requirement: API, rastreamento e operacao
O sistema SHALL versionar a API pelo grupo de API do Xano, cuja URL base identifica a versao publicada; o prefixo `/api/v1/` nao e exigido. A geracao de identificador de rastreamento por requisicao e sua correlacao com logs, auditoria, e-mail e erros ficam fora do MVP e registradas no backlog. O sistema SHALL monitorar erros de API, rotinas manuais, e-mails, documentos, filas e tentativas bloqueadas e SHALL possuir procedimento de backup e restauracao documentado e testado ao menos uma vez.

#### Scenario: Falha operacional detectada
- **WHEN** uma rotina manual tem itens pendentes ou uma fila acumula itens acima do limite
- **THEN** o sistema disponibiliza o indicador operacional correspondente e permite diagnostico

#### Scenario: Restauracao testada
- **WHEN** o procedimento de backup documentado e executado e restaurado em um workspace de teste
- **THEN** o schema e os dados restaurados correspondem ao backup, e o resultado fica registrado nas evidencias do projeto
