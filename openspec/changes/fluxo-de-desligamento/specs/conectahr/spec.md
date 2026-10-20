## ADDED Requirements

### Requirement: Checklist de saída do desligamento
O sistema SHALL criar, ao aprovar um desligamento, os itens do checklist de saída (devolução de equipamentos, revogação de acessos, entrevista de desligamento e cálculo das verbas rescisórias), cada um com a área responsável. O RH SHALL poder marcar cada item como feito ou pendente, nunca no próprio desligamento, e cada marcação SHALL ficar na auditoria. A conclusão de um desligamento agendado SHALL exigir todos os itens feitos.

#### Scenario: Itens na aprovação
- **WHEN** o RH aprova um desligamento com aviso prévio
- **THEN** o pedido fica agendado com os quatro itens do checklist pendentes

#### Scenario: Concluir com checklist incompleto
- **WHEN** o RH tenta concluir um desligamento agendado com um item pendente, na data efetiva
- **THEN** o backend recusa e informa quantos itens faltam

### Requirement: Pedido de desligamento por qualquer pessoa com ficha
O sistema SHALL permitir que qualquer pessoa com ficha de colaborador ativa peça o próprio desligamento, qualquer que seja o perfil, e que o gestor do departamento peça o de alguém da equipe. A decisão SHALL continuar com o RH, e ninguém SHALL decidir o próprio pedido.

#### Scenario: RH pede o próprio desligamento
- **WHEN** uma pessoa com perfil RH pede o próprio desligamento
- **THEN** o pedido fica pendente e outra pessoa do RH decide

#### Scenario: Pedido para alguém de fora da equipe
- **WHEN** alguém pede o desligamento de uma pessoa de um departamento que não gere
- **THEN** o backend recusa
