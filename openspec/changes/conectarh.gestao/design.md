## Context

A proposta introduz uma plataforma nova e ainda nao ha codigo ou especificacoes existentes no repositorio. O modelo de referencia contem usuarios, colaboradores, cargos, departamentos, historico profissional, ponto, documentos, ferias, ausencias e entidades de avaliacao. Os registros mostrados nas imagens sao dados de teste e nao devem ser migrados.

O produto deve demonstrar backend avancado com Xano e Script Xano, desenvolvimento web com Reflex, especificacao com OpenSpec, colaboracao via GitHub, integracao frontend-backend, deploy e validacao de mercado.

## Goals / Non-Goals

**Goals:**

- Separar identidade, autorizacao e dominio de RH, mantendo contratos claros entre os modulos.
- Proteger credenciais, sessoes, documentos pessoais e feedbacks privados.
- Implementar fluxos de estado rastreaveis para ponto, ferias, ausencias, documentos e avaliacao.
- Permitir notificacoes assincronas e reprocessaveis por e-mail.
- Implementar o ciclo de desligamento (solicitacao, analise, decisao e encerramento de acesso) dentro do MVP, mantendo rastreabilidade completa no historico profissional.
- Entregar incrementos demonstraveis para as avaliacoes parciais e um pacote final de apresentacao, README e evidencias de validacao.
- Priorizar no MVP central de pendencias, onboarding, auditoria, regras por contrato e excecoes individuais como primeira fatia entregavel; entregar os demais recursos especificados (sessoes e dispositivos, delegacao e calendario, quarentena e retencao de documentos, reconhecimento e desenvolvimento, indicadores e exportacoes, operacao e rastreamento) tambem dentro do MVP, na ordem de fatias verticais registrada em Risks / Trade-offs.

**Non-Goals:**

- Importar os registros de exemplo das telas.
- Implementar folha de pagamento, beneficios, recrutamento ou integracoes externas de ponto nesta mudanca.
- Implementar Streamlit; o frontend escolhido para o projeto e exclusivamente Reflex.

## Decisions

### Identidade e seguranca

Usar sessoes com access token de curta duracao, expiracao fixa de uma hora e registro server-side de sessoes revogadas para suportar logout imediato. Senhas devem ser armazenadas somente com hash adaptativo; tokens de redefinicao e codigos de acesso devem ser tratados como segredos, com expiracao, uso unico e protecao contra enumeracao de contas. Alternativas consideradas: sessoes longas sem revogacao, rejeitadas por dificultarem logout e aumentarem o impacto de vazamentos.

A validacao padrao de login do ConectaRH e um codigo numerico de 6 digitos enviado por e-mail via SendGrid a cada login, obrigatorio para todas as contas. O codigo expira em 5 minutos, e a validacao bloqueia apos 5 tentativas invalidas, exigindo novo login para gerar outro codigo. Alternativa considerada: TOTP via aplicativo autenticador, rejeitado por exigir instalar e configurar um app antes do primeiro uso, adicionando friccao logo no onboarding, alem de o time ja ter familiaridade operacional com SendGrid. Trade-off aceito conscientemente: um codigo por e-mail depende da seguranca da propria caixa de entrada do usuario — aceitavel para o escopo atual do projeto.

A troca de senha temporaria sera uma etapa de estado da sessao. O backend deve rejeitar qualquer rota funcional enquanto a flag de primeiro acesso estiver ativa.

### Autorizacao

Adotar autorizacao por politica de perfil e escopo organizacional, aplicada em todo endpoint na camada de API (nao apenas na interface). O perfil define a acao e o relacionamento colaborador-gestor-departamento limita o conjunto de registros. Alternativas consideradas: somente verificacoes no frontend, rejeitadas porque nao protegem APIs; ACL independente por tela, rejeitada por duplicar regras e facilitar divergencias.

Decisao revista: a politica e replicada explicitamente em cada endpoint (uma `precondition` de perfil, ou escopo por identidade via `$auth.id`/`colaborador_id`), em vez de centralizada numa function ou middleware compartilhado como planejado originalmente. Motivo: a memoria de quirks da plataforma registra que chamada function-to-function e nao confiavel neste workspace Xano, e chamada query-to-function nunca foi confirmada em runtime; nao valia o risco de quebrar ~90 endpoints ja funcionando por uma abstracao nao testada (Xano Middleware existe como primitiva, mas o mecanismo de anexa-lo a um grupo de API inteiro via XanoScript textual nao foi encontrado nem testado). Verificado nesta sessao por auditoria de todo o codigo: dos 92 endpoints de negocio (excluindo os 10 arquivos de definicao de `api_group`), 80 tem checagem explicita de perfil e os demais sao naturalmente escopados por identidade (ex.: `minhas_solicitacoes`, `meu_ponto`, `meus_comunicados` sempre filtram pelo `colaborador_id`/`user_id` do proprio chamador) — nenhum endpoint aceita uma requisicao fora do escopo autorizado. O requisito funcional (autorizacao aplicada na API, nao so na interface) esta atendido; a centralizacao arquitetural fica como debito tecnico documentado, nao um requisito de comportamento.

Vinculos de gestao terao vigencia, permitindo troca de gestor, substituicao temporaria e preservacao do historico. Delegacoes de aprovacao terao titular, substituto, periodo, permissoes delegadas, motivo e expiracao automatica. Nenhum usuario podera aprovar sua propria solicitacao.

Regras normativas nao serao alteracoes diretas no cadastro do colaborador. `instrumento_normativo` armazenara origem, tipo, vigencia, documento comprobatório, status e aprovadores. Para instrumentos coletivos, serao mantidos separadamente `numero_solicitacao_mediador`, `numero_registro_mte` e `numero_processo_mte`, com formatos validados. `regra_override` armazenara parametro, valores anterior e novo, prioridade, abrangencia, vigencia, justificativa e instrumento de origem. Cada alteracao criara nova versao; regras vigentes serao imutaveis.

A resolucao considerara somente regras vigentes, verificara abrangencia, prioridade e especificidade e bloqueara a publicacao de conflitos nao resolvidos. RH ou responsavel juridico devera aprovar a prioridade; o sistema nao inferira qual norma prevalece juridicamente. Convencoes e acordos coletivos deverao registrar o identificador do Sistema Mediador.

Acordos coletivos, convencoes coletivas e termos aditivos somente poderao ser ativados como `vigente` quando possuirem os tres identificadores, data de registro, vigencia, categoria, abrangencia territorial, documento oficial e aprovacao interna. Sem registro no MTE, permanecerao pendentes. Termos aditivos tambem referenciarao o instrumento principal e suas clausulas alteradas. Instrumentos vencidos nao serao usados em novos calculos.

### Dados bancarios do colaborador

O colaborador cadastra e atualiza os proprios dados bancarios (banco, agencia, conta, digito e tipo de conta — corrente ou poupanca) diretamente em seu cadastro, sem depender do RH para o cadastro inicial. RH e Admin consultam esses dados somente para fins de pagamento; nenhum dos dois perfis edita os dados em nome do colaborador — uma correcao exige que o proprio colaborador atualize o registro. Gestor nao tem acesso aos dados bancarios de sua equipe, seguindo o mesmo principio de minimizacao ja aplicado a dados medicos e documentos sensiveis.

Nao havera historico versionado (equivalente ao `historico_profissional`) para alteracoes bancarias: o registro mantem somente o valor vigente, e cada alteracao gera um evento na auditoria geral (`auditoria`) com autor, data e valores anterior/novo. Alternativa considerada: versionar como evento de historico profissional, rejeitada por ser dado operacional (nao contratual) cuja trilha de auditoria generica ja atende a rastreabilidade exigida.

### Persistencia e integridade

Usar um banco relacional com chaves estrangeiras, restricoes de dominio, indices para consultas por colaborador, gestor, departamento, periodo e status, e transacoes para decisoes que alteram cadastro, historico e auditoria. Os enums devem ser representados por tipos controlados no dominio e validados tambem na persistencia. Arquivos devem ficar fora da tabela de negocio, em armazenamento de objetos privado, mantendo no banco somente metadados, hash, tamanho, tipo, chave e estado. A jornada e as ferias devem consultar a matriz inicial por tipo de contrato definida na especificacao, com configuracao manual para `OUTRO` e possibilidade de ajustes autorizados por contrato, acordo ou norma aplicavel.

A matriz inicial sera: CLT com 8 horas/dia, 44 horas/semana, periodo aquisitivo de 12 meses, 30 dias, proporcional, solicitacao habilitada e ate 3 periodos; PJ sem aplicacao de jornada ou ferias no sistema; ESTAGIO com 6 horas/dia, 30 horas/semana, 12 meses, 30 dias de recesso, proporcional, solicitacao habilitada e 1 periodo; APRENDIZ com 6 horas/dia, 30 horas/semana, 12 meses, 30 dias, proporcional, solicitacao habilitada e 1 periodo; TEMPORARIO com 8 horas/dia, 44 horas/semana, ferias proporcionais e solicitacao desabilitada por padrao; e OUTRO com todos os campos configuraveis manualmente.

Para CLT, a referencia inicial e o Decreto-Lei nº 5.452, especialmente os arts. 58, 130, 134, 140, 146 e 147. A configuracao nao substitui validacao juridica de acordos coletivos, regimes especiais ou legislacao especifica de estagio e trabalho temporario.

### Fluxos de estado

Cada solicitacao tera estado explicito e transicoes permitidas, com decisao imutavel em trilha de auditoria. As operacoes de aprovacao, recusa e cancelamento devem ser idempotentes mediante identificador de comando ou verificacao de estado. O ponto conservara marcadores originais e ajustes posteriores para impedir perda de evidencia.

### Desligamento

O desligamento segue um fluxo de estados explicito: `pendente` -> `em_analise` -> (`concluido` para desligamento imediato ou `agendado` para aviso previo) -> `concluido`, com `rejeitada` e `cancelada` como saidas alternativas a partir dos estados abertos. Colaborador ou Gestor podem abrir a solicitacao somente para si mesmo ou para colaboradores do proprio departamento; a aprovacao e exclusiva do RH. A conclusao, seja imediata ou ao final do aviso previo, deve ocorrer em uma unica transacao que atualiza `colaborador.status` para `Desligado`, registra a data efetiva, desativa o acesso do usuario vinculado e cria um evento em `historico_profissional` com `tipo_alteracao = desligamento`. Uma solicitacao pendente, em analise ou agendada bloqueia a criacao de uma nova solicitacao para o mesmo colaborador. Uma rotina diaria deve concluir automaticamente os desligamentos `agendado` cuja `data_efetiva` foi atingida, de forma idempotente, sem reativar colaboradores nem duplicar o evento de historico.

Excecao aceita conscientemente e permanente: o plano Xano deste workspace nao inclui Background Tasks, e o usuario decidiu nao fazer upgrade. A rotina diaria automatica fica descartada como caminho de implementacao (arquivo de referencia mantido em `xano-workspace/task/concluir_desligamentos_agendados.xs`, com sintaxe validada por dry-run, mas nunca publicavel neste plano). `solicitacoes_desligamento/{id}/concluir POST` reproduz a mesma transacao para conclusao **manual** pelo RH, com a mesma trava de que a `data_efetiva` precisa ter chegado, e e o comportamento definitivo do MVP — nao um contorno temporario. O mesmo padrao (endpoint de acao manual do RH substituindo qualquer "rotina diaria automatica") se aplica a todo outro requisito equivalente do projeto, a comecar pelo vencimento de documentos (item 5.3).

### Regras legais e limites do MVP

O cadastro CLT deve bloquear inicio de atividades sem registro e manter campos contratuais, vigencia e responsavel. Integrações futuras com eSocial e CTPS Digital devem respeitar os prazos aplicáveis, incluindo admissão até a véspera e anotação contratual em até cinco dias úteis, sem inventar confirmação quando o serviço externo estiver indisponível.

O cálculo CLT deve respeitar a matriz aprovada, limites de jornada, intervalo, descanso, horas extras e trabalho noturno. O intervalo não será preenchido automaticamente como realizado. Banco de horas só será habilitado com fundamento registrado e controlará créditos, débitos, compensação, expiração e saldo na rescisão.

Estágio exigirá termo de compromisso, instituição de ensino e estudante, contabilizará atividades práticas e teóricas, aceitará jornada de até 6 horas/dia e 30 horas/semana ou configuração legal aplicável, e tratará recesso proporcional sem convertê-lo em vínculo CLT. Aprendiz exigirá contrato e programa de aprendizagem, limitará jornada geral a 6 horas, bloqueará horas extras/compensação indevida e aplicará proteções de menor quando pertinentes. Trabalho temporário exigirá contrato escrito, empresa de trabalho temporário, tomadora, motivo e prazo; PJ não terá ponto, férias ou subordinação de empregado aplicados automaticamente.

O registro de ponto será apresentado como controle interno experimental no MVP. A classificação como registrador eletrônico oficial exigirá projeto separado de conformidade com Portaria nº 671/2021, requisitos do REP aplicável, comprovante ao trabalhador, arquivos exigidos, atestado técnico e termo de responsabilidade.

Documentos médicos, biometria e filiação sindical serão tratados como dados sensíveis. Gestores receberão somente a informação operacional necessária, como apto/inapto quando cabível; diagnósticos e prontuários ficarão restritos a profissionais autorizados. ASO e prazos relacionados ao PCMSO serão metadados controlados, não prontuário médico comum.

### Documentos vencidos

Adicionar `documento.status` com os valores `pendente_analise`, `aprovado`, `rejeitado`, `vencido`, `substituido` e `arquivado`. RH aciona manualmente `documentos/processar_vencimentos POST`, que localiza documentos aprovados cuja `data_validade` terminou e executa a transicao `aprovado -> vencido` (mesma decisao de plataforma que a rotina de desligamento: sem Background Tasks neste plano Xano). O documento vencido deixa de ser valido para atendimento de pendencia, mas permanece armazenado ate substituicao ou arquivamento; o vencimento nunca altera automaticamente o status do colaborador. O mesmo acionamento emite os alertas de 30, 15 e 7 dias antes e do dia do vencimento, por e-mail ao colaborador; `documento.ultimo_alerta_dias` guarda o menor limiar ja alertado para evitar reenvio quando o endpoint roda mais de uma vez no mesmo dia. A substituicao deve preservar o documento anterior e relaciona-lo ao novo.

### Documentos e arquivos

Uploads passarao por quarentena com os estados `enviado`, `em_verificacao`, `liberado` ou `bloqueado`. A verificacao devera conferir extensao, tipo real, tamanho, hash, duplicidade, integridade e resultado de seguranca antes da liberacao. Uma matriz de documentos obrigatorios sera configuravel por contrato, cargo, nivel, departamento, nacionalidade, idade e condicao profissional, incluindo validade, frente/verso, prazo, aprovacao e aplicabilidade.

A retencao sera parametrizada por tipo de documento, com finalidade, base, prazo, evento inicial, tratamento apos vencimento, anonimização quando permitida, eliminacao automatica ou revisao manual e bloqueio por processo ou fiscalizacao.

Anexos de instrumentos normativos tambem passarao pela quarentena de arquivos. A funcao local de CPF devera remover caracteres nao numericos, exigir onze digitos, rejeitar sequencias repetidas e validar os dois digitos verificadores antes de qualquer consulta externa.

### Documentos emitidos pelo RH

Holerite e informe de rendimentos sao tipos de documento emitidos pelo RH, nao pelo colaborador: `documentos POST` para esses tipos cria o registro direto como `aprovado` (RH ja e a autoridade sobre a informacao, nao ha o que analisar), sem `data_validade` (nao vencem, entao ficam fora da rotina de vencimento) e sem alterar o modelo de acesso ja existente — RH/ADMIN e o proprio colaborador, dado o carater sensivel de remuneracao. Nao ha calculo, emissao ou integracao de folha de pagamento nesta mudanca; o arquivo em si e gerado fora do ConectaRH e apenas anexado.

### Reconhecimento e feedback

Reaproveitar a tabela `reconhecimento` existente para os dois casos previstos na spec — reconhecimento publico entre colegas e feedback corretivo privado de gestor para colaborador — em vez de criar uma entidade dedicada. Os campos `remetente_user_id`, `destinatario_colaborador_id` e `visibilidade` (`publico`/`privado`) ja cobrem a modelagem necessaria. Alternativa considerada: entidade separada para feedback privado, rejeitada por duplicar campos (remetente, destinatario, competencia, moderacao) sem necessidade, ja que a unica diferenca real e a regra de visibilidade e o conteudo permitido.

A `visibilidade` sera determinada pela relacao entre remetente e destinatario, nao escolhida livremente: quando o remetente e o gestor do destinatario, o registro SHALL ser gravado como `privado`, podendo conter conteudo corretivo; quando o remetente e um colega (colaborador que nao e o gestor do destinatario), o registro SHALL ser gravado como `publico` e o conteudo SHALL ser restrito a reconhecimento positivo, sujeito a moderacao. Essa validacao ocorre na API no momento da criacao, nao no schema da tabela.

### Notificacoes

Publicar eventos de dominio em uma fila/outbox transacional. Um trabalhador de e-mail consumira eventos com tentativas, backoff e chave de idempotencia, usando SendGrid como provedor. Alternativas consideradas: envio sincrono durante a requisicao, rejeitado porque falhas externas fariam operacoes validas parecerem falhas e aumentariam a latencia; outro provedor, adiado porque SendGrid foi definido para o projeto.

### Privacidade

Aplicar minimizacao de dados, logs sem senha, token, codigo de acesso (OTP) ou conteudo de documento, controle de acesso por recurso e criptografia em transito e em repouso. Feedback privado nao deve aparecer em listagens publicas ou notificacoes detalhadas.

### Processo de desenvolvimento e entrega

Manter o GitHub como fonte de verdade para codigo, documentacao e artefatos OpenSpec, usando branches e pull requests para o trabalho colaborativo. Cada incremento deve passar por especificacao, implementacao, revisao, teste e registro de decisao. A entrega deve incluir MVP demonstravel, README, arquitetura, especificacoes, evidencias de testes, deploy e resultados de validacao de mercado.

O frontend sera implementado exclusivamente com Reflex. As APIs serao versionadas sob `/api/v1/` e cada requisicao tera um identificador de rastreamento compartilhado por API, logs, auditoria, e-mail, erros e tarefas assincronas.

### Design system e prototipacao

O Figma sera a fonte de verdade visual antes do desenvolvimento das telas. O design system devera definir tokens de cor, tipografia, espacamento, grid, responsividade, acessibilidade e componentes reutilizaveis com estados de carregamento, erro, vazio, sucesso, bloqueio e permissao. Os prototipos deverao cobrir os fluxos principais por perfil e servir de referencia para o handoff da implementacao em Reflex.

### Central de solicitacoes do colaborador

Uma nova entidade `solicitacao_rh` registra pedidos do colaborador dos tipos `alteracao_cadastral`, `declaracao`, `documento_avulso` e `outra`, com estado `recebida`, `em_analise`, `atendida` ou `indeferida`. A central agrega, apenas para leitura, o status das solicitacoes que ja tem fluxo proprio (ferias, ausencia, correcao de ponto) — nao ha migracao delas para a nova entidade, evitando duplicar regras ja implementadas. Aprovar uma solicitacao de `alteracao_cadastral` registra a decisao mas nao altera o cadastro automaticamente; RH aplica a mudanca pelo fluxo de cadastro existente, preservando o historico profissional e a trilha de auditoria ja definidos. Alternativa considerada: aplicar a alteracao automaticamente ao aprovar, rejeitada por contornar a validacao e o historico ja exigidos no cadastro.

### Notificacoes internas

Alem do envio por e-mail via outbox/SendGrid, cada evento notificavel (ferias aprovada, documento vencendo, avaliacao disponivel, solicitacao respondida) cria tambem um registro de notificacao interna vinculado ao usuario, marcavel como lida. A notificacao interna nao substitui o e-mail nem depende dele — ambos sao gerados a partir do mesmo evento de dominio.

### Experiencia e produtividade

Organograma, pesquisa global e timeline do colaborador sao vistas somente leitura sobre dados ja existentes (cargo, departamento, vinculo gestor-colaborador, historico profissional, ferias e avaliacoes concluidas) — nenhuma tabela nova e necessaria para esses tres. Comunicados internos e artigos de FAQ sao entidades de conteudo novas e simples (titulo, conteudo, publico-alvo ou categoria, vigencia quando aplicavel), mantidas por RH ou Admin.

## Risks / Trade-offs

- [Escopo amplo do MVP] -> Entregar por fatias verticais, priorizando identidade/autorizacao, cadastro, ponto, documentos, ferias/ausencias e avaliacao nessa ordem.
- [Regras trabalhistas variam por contexto] -> Manter calculos de jornada e ferias parametrizados por tipo de contrato; validar a matriz contratual antes da entrada em producao.
- [Arquivos podem conter dados sensiveis] -> Usar armazenamento privado, URLs temporarias, validacao de tamanho/tipo, antivirus quando disponivel e auditoria de downloads.
- [E-mail pode falhar ou atrasar] -> Usar outbox, retentativas, estado de entrega e monitoramento; a decisao de negocio nao depende do envio imediato.
- [Erros de escopo podem expor dados de RH] -> Testar combinacoes de perfil, gestor e departamento em API e interface, com negacao por padrao.
- [Escopo pode exceder as 40 horas de desenvolvimento autonomo] -> Priorizar um caminho demonstravel por perfil e manter funcionalidades secundarias em backlog, sem alterar os contratos essenciais.
- [Regras de retencao e seguranca de arquivos podem conflitar com obrigacoes legais] -> Permitir bloqueio de eliminacao, revisao manual e parametrizacao por tipo; validar a politica com RH e juridico.
- [Conflitos entre normas podem ter efeitos juridicos] -> Exigir aprovacao humana, prioridade explicita, simulacao de impacto e bloqueio de publicacao quando a resolucao for inconclusiva.

## Migration Plan

Como nao existem dados de producao no repositorio, iniciar com schema versionado e banco vazio, sem carga dos registros das imagens. Implantar primeiro tabelas, restricoes e auditoria; depois habilitar os modulos por feature flag. Fazer smoke tests com dados sinteticos, validar fluxos de recuperacao de senha e de codigo de acesso por e-mail em ambiente controlado e somente entao liberar os papeis progressivamente. Rollback deve desabilitar a flag e reverter a versao da aplicacao sem apagar evidencias de auditoria; migracoes destrutivas nao devem ser usadas no MVP.

