## ADDED Requirements

### Requirement: Conflito entre regras de override
O sistema SHALL considerar em conflito uma regra de override que tenha o mesmo parâmetro e a mesma prioridade de outra regra vigente, com valor diferente, vigência que se sobrepõe e pelo menos uma pessoa atingida pelas duas. O sistema SHALL mostrar os conflitos na simulação de impacto e SHALL recusar o envio para aprovação e a aprovação de uma regra em conflito, até que a prioridade ou o escopo seja ajustado.

#### Scenario: Simulação mostra o conflito
- **WHEN** o RH simula uma regra de antecedência de férias para o Departamento Comercial com a prioridade de uma regra vigente para o cargo Analista, de valor diferente
- **THEN** a simulação lista o conflito com a regra do cargo Analista e quantas pessoas do Comercial são atingidas pelas duas

#### Scenario: Conflito bloqueia a aprovação
- **WHEN** alguém tenta enviar para aprovação ou aprovar uma regra em conflito
- **THEN** o backend recusa e informa a regra em conflito

#### Scenario: Prioridade resolve
- **WHEN** o RH muda a prioridade da regra em rascunho para um valor diferente da regra vigente
- **THEN** o conflito deixa de existir e a regra pode seguir para aprovação

### Requirement: Rejeição e prioridade da regra de override
O sistema SHALL permitir que RH ou Admin rejeitem uma regra de override pendente de aprovação com um motivo de 5 a 1000 caracteres, nunca a própria, e que mudem a prioridade de uma regra em rascunho ou pendente. As duas ações SHALL ficar na auditoria.

#### Scenario: Rejeitar com motivo
- **WHEN** o Admin rejeita uma regra pendente criada pelo RH, com motivo
- **THEN** a regra fica rejeitada e o motivo fica na auditoria

#### Scenario: Não rejeita a própria
- **WHEN** quem criou a regra tenta rejeitá-la
- **THEN** o backend recusa
