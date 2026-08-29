## Purpose

Define o comportamento funcional e as regras de seguranca da plataforma ConectaRH para centralizar processos de pessoas, jornada, documentos, ausencias e desenvolvimento de colaboradores.

## ADDED Requirements

### Requirement: Autenticacao e ciclo de sessao
O sistema SHALL autenticar usuarios por credencial e emitir token de acesso com validade de uma hora. O sistema SHALL invalidar a sessao no logout, exigir nova autenticacao apos a saida e impedir o acesso com token expirado, revogado ou adulterado.

#### Scenario: Login valido
- **WHEN** um usuario ativo informa credenciais validas
- **THEN** o sistema emite uma sessao com token valido por uma hora e registra o ultimo acesso

#### Scenario: Token expirado ou revogado
- **WHEN** uma requisicao usa token expirado, revogado ou invalido
- **THEN** o sistema rejeita a requisicao e exige nova autenticacao

### Requirement: Primeiro acesso, redefinicao e segundo fator por e-mail
O sistema SHALL permitir que somente Admin ou RH cadastrem usuarios. O sistema SHALL marcar credenciais temporarias, obrigar a troca antes de liberar o uso normal e permitir redefinicao iniciada na tela de login. Apos validar e-mail e senha, o sistema SHALL exigir um segundo fator obrigatorio: um codigo numerico de 6 digitos enviado por e-mail, valido por 5 minutos, antes de emitir a sessao. O sistema SHALL bloquear a validacao do codigo apos 5 tentativas invalidas, exigindo novo login para gerar outro codigo, e SHALL permitir reenviar um novo codigo que substitui o anterior.

#### Scenario: Primeiro acesso com senha temporaria
- **WHEN** o usuario autentica com senha temporaria
- **THEN** o sistema libera somente a troca de senha e nao permite acessar os modulos ate a conclusao

#### Scenario: Login exige codigo por e-mail
- **WHEN** o usuario informa e-mail e senha validos
- **THEN** o sistema envia um codigo de 6 digitos por e-mail e so emite a sessao apos o codigo correto ser informado

#### Scenario: Codigo expirado ou com tentativas esgotadas
- **WHEN** o codigo informado esta expirado ou o usuario ja errou 5 vezes
- **THEN** o sistema recusa a validacao sem revelar qual condicao falhou e exige um novo login para gerar outro codigo

#### Scenario: Redefinicao solicitada no login
- **WHEN** o usuario solicita redefinicao para um e-mail cadastrado e ativo
- **THEN** o sistema envia um fluxo de redefinicao com token de uso unico e prazo limitado sem revelar se o e-mail existe

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

### Requirement: Cadastro e historico profissional
O sistema SHALL manter usuarios, colaboradores, cargos, departamentos e historico profissional, incluindo admissao, promocoes, alteracoes de departamento, salario, cargo, contrato e desligamento. O sistema SHALL validar os dominios informados: contratos CLT, PJ, ESTAGIO, APRENDIZ, TEMPORARIO e OUTRO; status Ativo, Ferias, Afastado e Desligado; e niveis l1 a l5.

#### Scenario: Alteracao profissional
- **WHEN** RH registra uma alteracao de cargo, salario, contrato ou departamento
- **THEN** o sistema atualiza o cadastro, cria um evento no historico com responsavel e preserva os valores anteriores

#### Scenario: Valor fora do dominio
- **WHEN** uma operacao informa tipo de contrato, status ou nivel nao permitido
- **THEN** o sistema rejeita a operacao com erro de validacao

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
O sistema SHALL permitir simular um override antes da publicação, exibindo colaboradores afetados, escopos, regra atual, regra nova, conflitos, início de vigência e processos futuros afetados. Ao calcular jornada, ponto ou férias, SHALL gravar regra aplicada, versão, instrumento, parâmetros e data do cálculo. Regras retroativas SHALL exigir justificativa e aprovação especial, e registros anteriores SHALL preservar a regra usada.

#### Scenario: Simulação antes da publicação
- **WHEN** RH solicita simulação de um override
- **THEN** o sistema apresenta o impacto previsto sem alterar regras vigentes

#### Scenario: Cálculo auditável
- **WHEN** o sistema conclui um cálculo de jornada, ponto ou férias
- **THEN** armazena a regra, versão, instrumento, parâmetros e data utilizados

#### Scenario: Instrumento expirado
- **WHEN** a vigência de um instrumento termina
- **THEN** o sistema marca-o como `expirado` e deixa de usá-lo em novos cálculos sem alterar registros anteriores

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

### Requirement: Protecao de dados pessoais, saude e ausencias
O sistema SHALL coletar somente documentos necessarios, informar finalidade, restringir acesso por perfil e necessidade, usar armazenamento privado e aplicar retencao conforme finalidade e obrigacao legal. Atestados, ASO, dados biometricos e filiação sindical SHALL ter protecao de dados sensiveis. Gestores SHALL visualizar somente informacao operacional necessaria, e o sistema SHALL controlar ausencias justificadas, injustificadas, medicas e eventos aplicaveis ao eSocial.

#### Scenario: Gestor consulta atestado
- **WHEN** um gestor consulta ausencia com documento medico
- **THEN** o sistema exibe apenas o estado operacional permitido e oculta diagnostico e conteudo clinico

#### Scenario: Documento fora da finalidade
- **WHEN** a finalidade de conservacao de um documento termina e nao existe bloqueio legal
- **THEN** o sistema encaminha o documento para eliminacao ou revisao conforme a politica, preservando auditoria

### Requirement: Avaliacao justa e nao discriminatoria
O sistema SHALL informar previamente criterios de avaliacao, impedir criterios discriminatorios, restringir avaliações privadas, aceitar apenas reconhecimento positivo no espaco publico, permitir contestacao ou revisao humana e impedir que decisoes automaticas promovam, punam ou desliguem pessoas. O sistema SHALL evitar rankings, recomendacoes ou restricoes baseados em raça, etnia, sexo, gravidez, idade, deficiencia, religiao, orientacao sexual, saude, filiação sindical ou opiniao politica.

#### Scenario: Criterio discriminatorio
- **WHEN** um administrador tenta usar atributo protegido em ranking ou recomendacao
- **THEN** o sistema rejeita a configuracao e registra o bloqueio

#### Scenario: Avaliacao contestada
- **WHEN** um colaborador contesta uma avaliacao concluida
- **THEN** o sistema abre revisao humana sem alterar retroativamente a avaliacao original

### Requirement: Auditoria obrigatoria
O sistema SHALL auditar autenticacao, logout, troca e redefinicao de senha, 2FA, usuarios, alteracoes contratuais, ponto e ajustes, decisoes, documentos, regras trabalhistas, exportacoes e alteracoes em avaliacoes concluidas, incluindo responsavel, data, justificativa e valores anterior e novo. O sistema SHALL negar por padrao, preservar historicos e nunca apagar evidencias silenciosamente.

#### Scenario: Operacao sensivel auditada
- **WHEN** ocorre uma alteracao de regra, documento, contrato, ponto ou avaliacao
- **THEN** o sistema cria evento com autor, contexto, valores e resultado consultavel por Admin ou RH

#### Scenario: Tentativa sem permissao
- **WHEN** um usuario tenta operar fora do seu escopo
- **THEN** o sistema nega por padrao e registra a tentativa conforme a politica

### Requirement: Registro de ponto e correcao
O sistema SHALL permitir registrar entrada, inicio e fim de intervalo e saida, acompanhar a jornada e calcular horas trabalhadas e extras quando aplicavel. O registro SHALL usar os status ABERTO, COMPLETO, INCOMPLETO ou AJUSTADO. O colaborador SHALL poder solicitar correcao, e o responsavel autorizado SHALL poder aprovar ou recusar com justificativa.

#### Scenario: Jornada concluida
- **WHEN** o colaborador registra os marcadores necessarios do dia
- **THEN** o sistema calcula a jornada e marca o registro como COMPLETO

#### Scenario: Correcao aprovada
- **WHEN** o responsavel com permissao aprova uma solicitacao de correcao
- **THEN** o sistema ajusta o registro, preserva o valor original, registra a decisao e marca o registro como AJUSTADO

### Requirement: Documentos e pendencias
O sistema SHALL permitir que colaboradores enviem documentos associados ao seu cadastro e que RH solicite documentos pendentes. O sistema SHALL manter tipo, metadados, validade, observacoes, estado e responsaveis, proteger os arquivos e notificar pendencias por e-mail. `documento.status` SHALL aceitar somente `pendente_analise`, `aprovado`, `rejeitado`, `vencido`, `substituido` ou `arquivado`. Uma rotina diaria SHALL alterar documentos `aprovado` para `vencido` quando a `data_validade` terminar. O documento vencido SHALL deixar de ser valido, permanecer armazenado e nao SHALL desativar o colaborador.

#### Scenario: Documento enviado
- **WHEN** um colaborador envia um arquivo permitido para um tipo de documento
- **THEN** o sistema armazena o arquivo protegido, associa-o ao colaborador e informa o recebimento

#### Scenario: Pendencia solicitada
- **WHEN** RH solicita um documento ausente ou vencido
- **THEN** o sistema cria a pendencia, define prazo e envia notificacao ao colaborador

#### Scenario: Documento aprovado vencido
- **WHEN** a rotina diaria encontra um documento aprovado cuja data de validade terminou
- **THEN** altera o status para `vencido`, preserva o arquivo e sinaliza a necessidade de substituicao sem alterar o status do colaborador

#### Scenario: Alertas de vencimento
- **WHEN** um documento aprovado se aproxima da data de validade em 30, 15 ou 7 dias, ou chega ao dia do vencimento
- **THEN** o sistema envia o alerta correspondente por e-mail

#### Scenario: Documento substituido ou arquivado
- **WHEN** RH ou colaborador autorizado envia uma substituicao ou arquiva um documento vencido
- **THEN** o sistema preserva o documento anterior, registra a relacao ou motivo e atualiza o status permitido

### Requirement: Ferias e ausencias
O sistema SHALL permitir solicitar ferias e registrar ausencias com acompanhamento de status. Ferias SHALL usar Pendente, Aprovada, Rejeitada, Cancelada ou Concluida. Ausencias SHALL usar Falta, Atestado, Afastamento, Licenca ou Outro e status Pendente, Aprovada, Rejeitada ou Registrado. RH e Gestor SHALL decidir ferias conforme o escopo, mantendo justificativa e responsavel.

#### Scenario: Ferias aprovadas
- **WHEN** RH ou Gestor autorizado aprova uma solicitacao pendente
- **THEN** o sistema valida o periodo, registra a decisao e altera o status para Aprovada

#### Scenario: Ausencia registrada
- **WHEN** uma ausencia e criada com tipo permitido e periodo valido
- **THEN** o sistema registra o evento e apresenta seu status conforme o fluxo aplicavel

### Requirement: Avaliacoes, feedbacks, metas e PDI
O sistema SHALL suportar ciclos de avaliacao, competencias, respostas, metas anuais, progresso, conclusao e PDI. Feedback entre gestor e colaborador SHALL ser privado; feedback entre colaboradores SHALL ser publico, sujeito a moderacao e visivel conforme o tipo definido.

#### Scenario: Meta acompanhada
- **WHEN** um colaborador cria uma meta em ciclo ativo e atualiza seu progresso
- **THEN** o sistema registra indicador, valor esperado, prazo, percentual, comentarios e resultado final

#### Scenario: Feedback privado
- **WHEN** um gestor envia feedback ao colaborador avaliado
- **THEN** somente participantes autorizados e RH conforme permissao conseguem consultar o conteudo

#### Scenario: Feedback publico
- **WHEN** um colaborador envia reconhecimento ou feedback a outro colaborador
- **THEN** o sistema publica o conteudo conforme regras de visibilidade e permite moderacao registrada

### Requirement: Auditoria e notificacoes
O sistema SHALL registrar eventos sensiveis, incluindo autenticacao, alteracoes cadastrais, decisoes, acessos a documentos e moderacao. Notificacoes de pendencias, decisoes e eventos de prazo SHALL ser entregues por e-mail sem expor dados sensiveis no assunto ou em links sem protecao.

#### Scenario: Decisao rastreavel
- **WHEN** uma solicitacao de ponto, ferias ou ausencia e aprovada, recusada ou cancelada
- **THEN** o sistema registra autor, data, acao, justificativa e estado anterior e posterior

#### Scenario: Falha no envio de e-mail
- **WHEN** o provedor de e-mail nao aceita uma notificacao
- **THEN** o sistema preserva a pendencia, registra a falha e permite reprocessamento sem duplicar a decisao

### Requirement: Central de tarefas e pendencias
O sistema SHALL apresentar uma central personalizada por perfil com documentos aguardando envio ou analise, ferias e correcoes de ponto pendentes, avaliacoes nao respondidas, metas e PDIs atrasados e pendencias de senha temporaria ou 2FA.

#### Scenario: Central do colaborador
- **WHEN** um colaborador acessa sua central
- **THEN** o sistema exibe somente suas pendencias e as acoes autorizadas para resolve-las

#### Scenario: Central do gestor ou RH
- **WHEN** um gestor ou RH acessa sua central
- **THEN** o sistema exibe pendencias sob seu escopo e tarefas de aprovacao ou analise correspondentes

### Requirement: Onboarding de colaborador
O sistema SHALL oferecer checklist de admissao com dados pessoais, acesso, troca de senha, 2FA, documentos obrigatorios, aprovacoes, gestor, departamento, contrato, jornada, metas iniciais e acompanhamentos de 30, 60 e 90 dias.

#### Scenario: Onboarding acompanhado
- **WHEN** RH inicia o onboarding de um colaborador
- **THEN** o sistema cria o checklist, calcula o progresso e aponta os itens pendentes por responsavel

#### Scenario: Item de onboarding concluido
- **WHEN** uma etapa e concluida por usuario autorizado
- **THEN** o sistema registra data, responsavel e evidencia sem permitir conclusao indevida fora do fluxo

### Requirement: Auditoria consultavel
O sistema SHALL permitir que Admin e RH consultem autor, acao, registro afetado, valor anterior, valor novo, data, horario, IP ou sessao, justificativa e resultado da operacao.

#### Scenario: Consulta de auditoria
- **WHEN** Admin ou RH filtra eventos auditados
- **THEN** o sistema retorna os detalhes permitidos e respeita filtros de periodo, usuario, recurso e resultado

#### Scenario: Auditoria restrita
- **WHEN** um Colaborador ou Gestor tenta consultar o painel administrativo
- **THEN** o sistema nega o acesso e registra a tentativa conforme a politica de seguranca

### Requirement: Regras contratuais e excecoes individuais
O sistema SHALL permitir que regras de jornada e ferias sejam administradas por tipo de contrato com horas diarias, horas semanais, periodo aquisitivo, dias, proporcionalidade, fracionamento, limite de periodos, antecedencia, obrigatoriedade de ponto, habilitacao de solicitacao e vigencia inicial e final. O sistema SHALL permitir excecoes individuais auditadas com jornada, escala, horas, ferias, vigencia, justificativa e autorizador.

#### Scenario: Regra vigente aplicada
- **WHEN** o sistema calcula jornada ou valida ferias
- **THEN** usa a regra contratual vigente na data do evento, sem alterar calculos historicos

#### Scenario: Excecao individual aplicada
- **WHEN** RH autoriza uma excecao para um colaborador dentro de sua vigencia
- **THEN** o sistema aplica a excecao, preserva a regra original e registra justificativa e autorizador

### Requirement: Delegacao, prazos e calendario
O sistema SHALL suportar delegacao temporaria de aprovacao, com titular, substituto, vigencia, permissoes, motivo, expiracao automatica e bloqueio de autoaprovacao. O sistema SHALL controlar prazos e escalonar atrasos. O calendario SHALL reunir feriados, dias nao uteis, ferias, ausencias, ciclos, vencimentos e prazos e ser considerado nos calculos aplicaveis.

#### Scenario: Delegacao vigente
- **WHEN** o substituto atua durante uma delegacao vigente
- **THEN** o sistema permite somente as permissoes delegadas e registra titular, substituto e decisao

#### Scenario: Prazo vencido
- **WHEN** uma pendencia ultrapassa seu prazo
- **THEN** o sistema marca como atrasada, notifica o responsavel e escalona ao nivel superior quando configurado

#### Scenario: Conflito de ferias
- **WHEN** uma ferias e analisada
- **THEN** o sistema verifica sobreposicoes, ausencias, saldo, antecedencia, periodo aquisitivo e disponibilidade minima da equipe e gera alerta conforme a politica

### Requirement: Sessoes e dispositivos
O sistema SHALL permitir consultar sessoes ativas, ultimo acesso, dispositivo ou navegador, tentativas recentes e encerrar uma sessao ou todas as demais. O sistema SHALL alertar acessos suspeitos.

#### Scenario: Encerramento de dispositivo
- **WHEN** o usuario encerra uma sessao especifica
- **THEN** o token daquela sessao e revogado sem encerrar as demais

### Requirement: Quarentena e retencao de documentos
O sistema SHALL processar anexos pelos estados `enviado`, `em_verificacao`, `liberado` ou `bloqueado`, validando extensao, tipo real, tamanho, hash, duplicidade, corrupcao e verificacao de seguranca antes da liberacao. O sistema SHALL manter politica de retencao por tipo de documento com finalidade, base, prazo, evento inicial, tratamento, anonimização, eliminacao ou revisao e bloqueio por processo.

#### Scenario: Arquivo liberado
- **WHEN** o anexo passa por todas as verificacoes
- **THEN** o sistema altera o estado para `liberado` e permite seu uso conforme permissao

#### Scenario: Arquivo bloqueado
- **WHEN** o anexo falha em uma verificacao de seguranca ou integridade
- **THEN** o sistema altera o estado para `bloqueado`, impede o uso e registra o motivo

#### Scenario: Retencao impede eliminacao
- **WHEN** um documento esta sob bloqueio de processo ou revisao manual
- **THEN** o sistema impede a eliminacao automatica e preserva o historico

### Requirement: Desenvolvimento e reconhecimento
O sistema SHALL registrar reunioes individuais, check-ins e historico de metas, reconhecimento publico exclusivamente positivo, feedback corretivo privado, pesquisas anonimas de clima com resultados agrupados, matriz de competencias e plano de carreira sem promocao automatica.

#### Scenario: Check-in de meta
- **WHEN** colaborador ou gestor registra um check-in
- **THEN** o sistema preserva progresso, comentarios, dificuldades, evidencias, alteracoes de prazo e historico

#### Scenario: Reconhecimento moderado
- **WHEN** um colaborador envia reconhecimento a outro
- **THEN** o sistema aceita somente conteudo positivo, associa competencia, aplica moderacao e controla visibilidade

#### Scenario: Pesquisa com poucas respostas
- **WHEN** um grupo possui respostas abaixo da quantidade minima configurada
- **THEN** o sistema nao exibe o resultado individual ou agrupado daquele grupo

#### Scenario: Plano de carreira consultado
- **WHEN** o colaborador consulta sua carreira
- **THEN** o sistema exibe nivel atual, proximo nivel, competencias, lacunas, metas, PDI e evolucao sem promover automaticamente

### Requirement: Indicadores, exportacoes e preferencias
O sistema SHALL disponibilizar indicadores de colaboradores, contratos, ponto, ausencias, ferias, documentos, avaliacoes, metas, PDIs e aprovacoes. O sistema SHALL exportar CSV ou PDF respeitando permissoes e registrar a exportacao. O sistema SHALL permitir preferencias de canal e frequencia, sem desativar alertas obrigatorios de seguranca.

#### Scenario: Exportacao autorizada
- **WHEN** um usuario autorizado exporta um relatorio
- **THEN** o arquivo inclui somente dados do seu escopo e a exportacao e auditada

### Requirement: API, rastreamento e operacao
O sistema SHALL versionar as rotas sob `/api/v1/`, gerar identificador de rastreamento por requisicao e correlaciona-lo com logs, auditoria, e-mail, erros e tarefas assincronas. O sistema SHALL monitorar erros de API, tarefas, e-mails, documentos, filas, latencia e tentativas bloqueadas e SHALL possuir backup e recuperacao testados.

#### Scenario: Requisicao rastreavel
- **WHEN** uma requisicao dispara uma tarefa assincrona e um e-mail
- **THEN** o mesmo identificador permite correlacionar a requisicao, o log, a auditoria e o resultado do processamento

#### Scenario: Falha operacional detectada
- **WHEN** uma tarefa diaria falha ou uma fila acumula itens acima do limite
- **THEN** o sistema registra o incidente, disponibiliza alerta operacional e permite diagnostico

### Requirement: Acessibilidade e validacao de CPF
O frontend SHALL oferecer navegacao por teclado, contraste adequado, labels, foco visivel, mensagens compreensiveis, responsividade, textos alternativos e status que nao dependam somente de cor. O sistema SHALL validar CPF exclusivamente pelo algoritmo local, sem API externa.

#### Scenario: CPF valido
- **WHEN** um CPF e submetido ao cadastro
- **THEN** o sistema aceita o cadastro quando a validacao local for positiva

#### Scenario: CPF invalido ou servico indisponivel
- **WHEN** a validacao local for negativa
- **THEN** o sistema impede a conclusao do cadastro e informa o campo invalido sem expor dados sensiveis

### Requirement: Desligamento de colaborador
O sistema SHALL permitir que Colaborador ou Gestor solicitem o desligamento de um colaborador dentro do proprio escopo (a si mesmo ou a colaboradores do departamento sob sua gestao), com decisao exclusiva do RH. O sistema SHALL suportar desligamento `imediato` e `aviso_previo`, bloquear nova solicitacao enquanto existir uma pendente, em analise ou agendada para o mesmo colaborador, e concluir automaticamente os desligamentos agendados quando a data efetiva for atingida.

#### Scenario: Solicitacao dentro do escopo
- **WHEN** um Colaborador solicita o proprio desligamento ou um Gestor solicita o desligamento de um colaborador do seu departamento
- **THEN** o sistema cria a solicitacao como `pendente` e impede solicitacao para colaborador fora do escopo do solicitante

#### Scenario: Aprovacao exclusiva do RH
- **WHEN** RH aprova uma solicitacao em analise
- **THEN** o sistema conclui o desligamento imediato ou agenda a data efetiva para aviso previo, conforme o tipo da solicitacao

#### Scenario: Conclusao do desligamento
- **WHEN** um desligamento imediato e aprovado ou um desligamento agendado atinge a data efetiva
- **THEN** o sistema atualiza o status do colaborador para Desligado, desativa o acesso do usuario vinculado e registra o evento no historico profissional

#### Scenario: Solicitacao duplicada
- **WHEN** ja existe uma solicitacao pendente, em analise ou agendada para o colaborador
- **THEN** o sistema rejeita a criacao de uma nova solicitacao para o mesmo colaborador
