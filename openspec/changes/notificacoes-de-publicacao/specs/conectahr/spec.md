## ADDED Requirements

### Requirement: Aviso de treinamento novo
O sistema SHALL avisar no sino o público de um treinamento quando ele é criado ativo ou reativado: todos os colaboradores ativos, ou só os dos departamentos escolhidos. O sistema SHALL deixar de fora quem publicou e quem desligou o assunto "Treinamentos" nas preferências.

#### Scenario: Treinamento para um departamento
- **WHEN** o RH cria um treinamento ativo para o departamento Operações
- **THEN** cada colaborador ativo de Operações recebe "Novo treinamento disponível", e ninguém de TI recebe

#### Scenario: Quem publicou
- **WHEN** o RH que criou o treinamento também é do público
- **THEN** ele não recebe o aviso

#### Scenario: Preferência desligada
- **WHEN** a pessoa desligou "Treinamentos" em Configurações → Notificações
- **THEN** ela não recebe o aviso no sino

### Requirement: Convite de pesquisa sem vínculo com a resposta
O sistema SHALL avisar o público uma única vez, quando uma pesquisa de clima ou uma avaliação psicossocial fica disponível para resposta, e no início de cada ciclo do termômetro de humor. Ler ou abrir o convite SHALL NOT registrar participação, e nenhuma consulta SHALL ligar o convite à resposta.

#### Scenario: Pesquisa aberta
- **WHEN** o RH adiciona as perguntas a uma pesquisa de clima que já está no período
- **THEN** cada colaborador ativo recebe "Nova pesquisa", uma vez só

#### Scenario: Anonimato
- **WHEN** a pessoa abre o convite e responde a pesquisa
- **THEN** a resposta continua só na contagem anônima, e o convite não guarda nada sobre ela

### Requirement: Aviso para quem decide
Toda solicitação que espera a decisão de alguém SHALL gerar um aviso `pedido_novo` para quem decide, conforme a tabela "evento → quem recebe" do design. Uma delegação SHALL avisar o substituto, e o substituto com delegação ativa SHALL receber os pedidos do titular.

#### Scenario: Delegação
- **WHEN** um gestor delega as aprovações de férias a um colega de 01/11 a 15/11
- **THEN** o colega recebe o aviso da delegação, e os pedidos de férias do período avisam também o colega
