## ADDED Requirements

### Requirement: Metas, PDI e reuniões 1:1 dos liderados diretos (F16)
O sistema SHALL mostrar ao Gestor, em "Metas da equipe", as metas, as ações de PDI e as reuniões 1:1 dos liderados diretos, que são as fichas cujo superior direto é a ficha dele. De cada meta e ação, SHALL mostrar só título, prazo, progresso e situação, nunca salário, avaliação ou dados pessoais. O Gestor SHALL criar metas e ações de PDI só para os liderados diretos e para o departamento de que é gestor; SHALL registrar check-in nas metas dos liderados diretos, em nome dele; e SHALL agendar reuniões 1:1 só com os liderados diretos e depois marcá-las como realizadas ou canceladas. O backend SHALL recusar com 403 qualquer uma dessas ações fora desse escopo. O ciclo anual de metas e feedback SHALL continuar numa seção independente, sem virar metas percentuais nem check-ins.

#### Scenario: Gestor vê só os liderados diretos
- **WHEN** o Gestor abre "Metas da equipe"
- **THEN** vê as metas, o PDI e as reuniões 1:1 só dos liderados diretos, com título, prazo, progresso e situação, e a seção do ciclo anual separada

#### Scenario: Ação fora do escopo
- **WHEN** o Gestor tenta criar meta ou PDI, registrar check-in ou agendar 1:1 para quem não é liderado direto nem do departamento de que é gestor
- **THEN** o backend recusa com 403 e nada é gravado

#### Scenario: Check-in do líder
- **WHEN** o Gestor registra check-in na meta de um liderado direto
- **THEN** o check-in fica em nome dele e na auditoria, o liderado é avisado no sino e vê na Trajetória o progresso e quem registrou

#### Scenario: Reunião 1:1 agendada e cancelada
- **WHEN** o Gestor agenda uma 1:1 com um liderado direto e depois a cancela
- **THEN** o liderado recebe aviso no sino e por e-mail nas duas vezes e vê a reunião na Trajetória, com o motivo do cancelamento

#### Scenario: Fluxos anuais existentes
- **WHEN** liderança autorizada ou RH/Admin usa os formulários anuais
- **THEN** continuam disponíveis a seleção, a busca, a leitura das três etapas e o feedback, conforme a autorização retornada pelo backend, inclusive no modal compartilhado

### Requirement: Isolamento de estado das metas por sessão
O frontend SHALL vincular os caches de metas à identidade do usuário e ao token corrente, sem armazenar credenciais fora da memória da sessão. O sistema SHALL descartar caches, modal e campos de metas na troca ou no encerramento da sessão.

#### Scenario: Troca de conta ou token
- **WHEN** o usuário ou o token muda no mesmo navegador
- **THEN** os dados e campos anteriores não são reaproveitados, e a consulta ocorre com a sessão atual

#### Scenario: Falha de uma consulta
- **WHEN** uma consulta falha
- **THEN** o erro não é guardado no cache, a tela mostra a falha sem simular sucesso, e a outra seção da página continua funcionando

#### Scenario: Encerramento da sessão
- **WHEN** a pessoa sai ou a sessão expira
- **THEN** caches, formulário aberto, feedback digitado e seleções de metas são removidos
