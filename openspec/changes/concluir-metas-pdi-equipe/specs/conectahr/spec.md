## ADDED Requirements

### Requirement: F16 parcial separado do ciclo anual
O frontend SHALL apresentar ao Gestor a estrutura de Metas, PDI e reuniões 1:1 conforme o F16, distinguindo indisponibilidade de ausência comprovada de dados. O sistema SHALL preservar o ciclo anual em seção independente, sem converter respostas ou feedback anual em metas percentuais ou check-ins.

#### Scenario: Gestor acessa Metas da equipe
- **WHEN** o Gestor abre a página existente
- **THEN** encontra as abas Metas, PDI e Reuniões 1:1 com indisponibilidades explícitas e a seção funcional Ciclo anual de metas e feedback

#### Scenario: Contrato insuficiente ou inseguro
- **WHEN** uma ação depende de listagem excessiva, autorização departamental incompleta ou agendamento não suportado
- **THEN** a interface mantém a ação desabilitada e não chama plano_carreira, criação de metas, check-in de liderados ou PDI de outra pessoa

#### Scenario: Fluxos anuais existentes
- **WHEN** liderança autorizada ou RH/Admin utiliza os formulários anuais
- **THEN** continuam disponíveis seleção, busca, leitura das três etapas e feedback conforme a autorização retornada pelo backend, inclusive no modal compartilhado

### Requirement: Isolamento de estado das metas por sessão
O frontend SHALL vincular caches anuais à identidade do usuário e ao token corrente, sem armazenar credenciais fora da memória da sessão. O sistema SHALL descartar caches, modal e campos de metas na troca ou encerramento de sessão.

#### Scenario: Troca de conta ou token
- **WHEN** o usuário ou token muda no mesmo estado de navegador
- **THEN** dados e campos anuais anteriores não são reaproveitados e a consulta ocorre com a sessão atual

#### Scenario: Falha de uma consulta anual
- **WHEN** uma consulta falha
- **THEN** o erro não é cacheado e não remove a estrutura de indisponibilidade do F16 nem apresenta sucesso fictício

#### Scenario: Encerramento da sessão
- **WHEN** a pessoa sai ou a sessão expira
- **THEN** caches, formulário aberto, feedback digitado e seleções de metas são removidos
