## ADDED Requirements

### Requirement: Trajetória do colaborador
O sistema SHALL mostrar a cada pessoa com ficha de colaborador a própria trajetória: o nível atual, o próximo nível e as competências a desenvolver, sem nenhuma ação de promoção; a avaliação 360 do ciclo em andamento (autoavaliação, avaliação do gestor e avaliação de pares); as avaliações que ela tem a preencher; as avaliações enviadas sobre ela; as metas e as ações de PDI não concluídas nem canceladas; e os reconhecimentos recebidos, com o nome de quem enviou. O nome do avaliador SHALL aparecer só quando ele é o gestor ou o RH; avaliações de pares e de subordinados SHALL aparecer sem identificar o avaliador. Pela mesma tela, a pessoa SHALL poder responder e enviar as avaliações que lhe foram atribuídas, contestar uma avaliação enviada sobre ela, registrar check-in das próprias metas e atualizar o progresso do próprio PDI, sempre com a autorização decidida pelo backend.

#### Scenario: Carreira sem promoção automática
- **WHEN** uma pessoa no nível L2 abre a Trajetória
- **THEN** a tela mostra L2 como nível atual, L3 como próximo nível com as competências ativas de L3 e o aviso de que não há promoção automática, sem nenhum botão de promover

#### Scenario: Avaliação de pares anônima
- **WHEN** três pares foram designados para avaliar a pessoa no ciclo e dois enviaram
- **THEN** a tela mostra "2 de 3 respondidas" e nenhum nome de par

#### Scenario: Avaliação do gestor com nome
- **WHEN** o gestor da pessoa tem uma avaliação sobre ela no ciclo
- **THEN** a tela mostra o nome do gestor e se a avaliação está pendente ou enviada

#### Scenario: Responder e enviar
- **WHEN** a pessoa dá notas de 1 a 5 às competências de uma avaliação que lhe foi atribuída e envia
- **THEN** as respostas são gravadas, a avaliação fica enviada e sai da lista "Para você avaliar"

#### Scenario: Competências só para o avaliador
- **WHEN** alguém que não é o avaliador designado pede as competências de uma avaliação
- **THEN** o backend recusa, sem dizer se a avaliação existe

#### Scenario: Contestar
- **WHEN** a pessoa contesta uma avaliação enviada sobre ela, com motivo de pelo menos 5 caracteres
- **THEN** a contestação fica aberta para o RH e a avaliação passa a mostrar "Contestação em análise"

#### Scenario: Meta atrasada
- **WHEN** o prazo de uma meta não concluída já passou
- **THEN** a meta aparece com o selo "Atrasada" e o texto "Prazo era DD/MM/AAAA"

#### Scenario: Conta sem ficha de colaborador
- **WHEN** uma conta sem colaborador vinculado abre a Trajetória
- **THEN** a tela mostra a mensagem do backend em vez dos blocos
