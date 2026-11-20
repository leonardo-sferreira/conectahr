## ADDED Requirements

### Requirement: Resposta ao pedido do titular com resultado
O sistema SHALL registrar, ao responder um pedido LGPD do titular, o resultado: atendido, atendido em parte ou não atendido. A resposta ao titular SHALL ser obrigatória nos três casos, e o titular SHALL ver o resultado e a resposta. Ninguém SHALL responder o próprio pedido.

#### Scenario: Atendido em parte
- **WHEN** o RH atende um pedido LGPD com o resultado parcial e uma resposta
- **THEN** o pedido fica atendido, com o resultado "atendido em parte" e a resposta gravados, e o titular é avisado

#### Scenario: Atender sem resposta
- **WHEN** o RH tenta atender um pedido LGPD sem escrever a resposta ao titular
- **THEN** o backend recusa e nada muda

#### Scenario: Não atendido
- **WHEN** o RH indefere um pedido LGPD com a justificativa
- **THEN** o pedido fica indeferido com o resultado "não atendido"
