## ADDED Requirements

### Requirement: Termômetro de humor anônimo a cada 10 dias
O sistema SHALL perguntar a cada pessoa com ficha, uma vez por ciclo de 10 dias, como ela está se sentindo no trabalho, numa escala de 1 a 5 com um motivo opcional de uma lista fechada. O sistema SHALL guardar só contagens por ciclo, setor e nota (e por ciclo, setor e motivo), sem pessoa, data ou hora, e SHALL recusar uma segunda resposta no mesmo ciclo. RH e Admin SHALL ver os resultados de todos os setores, e o Gestor só os dos setores que gerencia. Nenhum grupo com menos respostas que o mínimo SHALL aparecer, nem por subtração.

#### Scenario: Responder uma vez por ciclo
- **WHEN** a pessoa responde o termômetro em 22/10/2026 e tenta responder de novo em 25/10/2026
- **THEN** a segunda resposta é recusada, e o cartão volta no Início em 31/10/2026

#### Scenario: Setor pequeno
- **WHEN** só um setor tem menos de 5 respostas no ciclo
- **THEN** esse setor e o menor dos outros aparecem como suprimidos, e o total da empresa continua visível

#### Scenario: Gestor de outro setor
- **WHEN** um gestor pede o resultado de um setor que não gerencia
- **THEN** o backend recusa
