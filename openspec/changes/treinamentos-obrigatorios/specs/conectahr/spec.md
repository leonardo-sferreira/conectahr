## ADDED Requirements

### Requirement: Catálogo e registro de treinamentos obrigatórios
O RH SHALL manter um catálogo de treinamentos com validade em meses e público (todos ou departamentos) e SHALL registrar a conclusão de uma turma de uma vez. O sistema SHALL calcular a validade de cada conclusão, SHALL recusar data de conclusão futura e SHALL avisar cada pessoa registrada. Cada criação, edição e registro SHALL ficar na auditoria.

#### Scenario: Turma com validade de 12 meses
- **WHEN** o RH registra a conclusão de um treinamento anual para três pessoas em 20/10/2026
- **THEN** as três conclusões ficam válidas até 20/10/2027 e cada pessoa recebe um aviso

#### Scenario: Data futura
- **WHEN** o RH tenta registrar uma conclusão com data de amanhã
- **THEN** o backend recusa

### Requirement: Situação dos treinamentos por pessoa
O sistema SHALL mostrar ao RH, para cada pessoa e treinamento obrigatório para o setor dela, se está em dia, vencendo (até 30 dias), vencido ou pendente, e SHALL mostrar à própria pessoa os treinamentos obrigatórios para ela, com a situação e o histórico.

#### Scenario: Treinamento de outro setor
- **WHEN** um treinamento é obrigatório só para Operações
- **THEN** a matriz não cobra esse treinamento de quem é de TI
