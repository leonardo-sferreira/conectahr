## ADDED Requirements

### Requirement: Pedido de alteração do tipo de acesso
O sistema SHALL permitir que só o Admin altere o tipo de acesso (perfil) de uma conta, inclusive pela ficha do colaborador, e SHALL permitir que o RH peça ao Admin outro tipo de acesso para uma conta, informando o perfil desejado e uma justificativa. O Admin SHALL aprovar (o perfil é trocado na hora) ou recusar com motivo, e quem pediu SHALL ser avisado da decisão. Ninguém SHALL pedir nem decidir sobre a própria conta, e SHALL haver no máximo um pedido pendente por conta. Toda etapa SHALL ficar na auditoria.

#### Scenario: RH pede acesso de Gestor
- **WHEN** o RH pede o perfil Gestor para a conta de um colaborador, com justificativa
- **THEN** o pedido fica pendente, os Admins são avisados e o perfil da conta não muda

#### Scenario: Admin aprova
- **WHEN** o Admin aprova o pedido pendente
- **THEN** o perfil da conta passa a ser o pedido, e o RH e a pessoa são avisados

#### Scenario: Admin recusa
- **WHEN** o Admin recusa o pedido com um motivo
- **THEN** o perfil não muda e o RH recebe o motivo

#### Scenario: Admin altera direto
- **WHEN** o Admin escolhe outro tipo de acesso na ficha do colaborador
- **THEN** o perfil é trocado na hora, sem pedido

#### Scenario: Admin não é escolhido na admissão
- **WHEN** o RH admite uma pessoa ou cria o acesso dela
- **THEN** o tipo de acesso oferece Colaborador, Gestor e RH, e o acesso Admin só pode ser dado depois, pela ficha do colaborador já cadastrado

#### Scenario: Pedido repetido
- **WHEN** o RH pede de novo para uma conta que já tem pedido pendente
- **THEN** o sistema recusa o novo pedido

#### Scenario: Admissão com tipo de acesso
- **WHEN** o RH admite uma pessoa escolhendo o tipo de acesso Gestor e cria a conta em seguida
- **THEN** a conta nasce Colaborador e o pedido de Gestor vai para o Admin
