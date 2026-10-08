## ADDED Requirements

**12. Proteção de Dados (LGPD)**

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
