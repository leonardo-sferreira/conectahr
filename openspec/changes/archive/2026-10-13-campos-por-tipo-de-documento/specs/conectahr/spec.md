## ADDED Requirements

### Requirement: Campos do documento por tipo
O envio de documento SHALL pedir só os campos do tipo escolhido (por exemplo: RG com número, órgão emissor, UF e data de expedição; CPF só com o número; comprovante de residência só com a data de emissão). O backend SHALL validar os campos obrigatórios de cada tipo, as opções fechadas, a UF, as datas e o CPF pelos dígitos verificadores, e SHALL recusar com mensagem clara sem gravar nada. O CPF informado nos tipos CPF e CIN SHALL ser igual ao da ficha do colaborador. Laudo de deficiência e ASO SHALL NOT pedir CID nem diagnóstico. A conferência do RH SHALL mostrar os dados informados ao lado do arquivo.

#### Scenario: Colaborador envia o RG
- **WHEN** o colaborador escolhe RG, informa número, órgão emissor, UF e data de expedição e anexa o arquivo
- **THEN** o documento é gravado com esses dados e o RH os vê na conferência

#### Scenario: Campo obrigatório em branco
- **WHEN** o colaborador envia uma CNH sem a validade
- **THEN** o sistema recusa com "Informe a validade." e não grava nada

#### Scenario: CPF diferente da ficha
- **WHEN** o colaborador envia o tipo CPF com um número válido que não é o da ficha dele
- **THEN** o sistema recusa com a mensagem de que o CPF não confere com o cadastro

#### Scenario: Comprovante de residência antigo
- **WHEN** o colaborador envia um comprovante de residência emitido há mais de 90 dias
- **THEN** o sistema recusa e pede um comprovante dos últimos 90 dias
