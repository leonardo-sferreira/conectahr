## ADDED Requirements

### Requirement: Documentos obrigatórios pré-definidos por contrato
O sistema SHALL vir com a matriz de documentos obrigatórios preenchida por tipo de contrato (CLT, Temporário, Aprendiz, Estágio e PJ), com prazo de envio, faixa de idade quando houver e prazo de guarda, e SHALL permitir que o RH acrescente regras por cargo ou departamento. A carga das regras SHALL poder ser repetida sem duplicar nem alterar regras que o RH já cadastrou. Um RG aprovado SHALL cumprir a regra da CIN e vice-versa.

#### Scenario: Estagiário
- **WHEN** o RH consulta os documentos obrigatórios de um estagiário maior de idade
- **THEN** a lista tem CPF, RG, comprovante de residência, declaração de matrícula e termo de compromisso de estágio, sem CTPS nem ASO

#### Scenario: Carga repetida
- **WHEN** a carga das regras roda de novo
- **THEN** nenhuma regra é duplicada e as do RH continuam como estão

#### Scenario: CIN no lugar do RG
- **WHEN** a pessoa tem a CIN aprovada e a regra pede RG
- **THEN** o RG não aparece como pendente
