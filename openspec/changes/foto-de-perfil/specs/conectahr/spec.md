## ADDED Requirements

### Requirement: Foto de perfil opcional
O colaborador SHALL poder enviar, trocar e remover a própria foto de perfil (JPG, PNG ou WebP de até 2 MB, gravada quadrada em 256 × 256, sem metadados). O sistema SHALL guardar a foto num bucket privado e SHALL mostrá-la, por URL assinada de curta duração, no perfil, no organograma e no avatar do topo. Sem foto, SHALL mostrar as iniciais. Ninguém SHALL trocar a foto de outra pessoa.

#### Scenario: Enviar a foto
- **WHEN** a pessoa envia uma foto JPG de 1 MB no "Meu perfil"
- **THEN** a foto aparece no perfil dela e, para outro usuário, no organograma

#### Scenario: Arquivo recusado
- **WHEN** a pessoa tenta enviar um PDF ou uma imagem de 5 MB
- **THEN** o envio é recusado com uma mensagem que diz o formato e o tamanho aceitos

#### Scenario: Foto de outra pessoa
- **WHEN** um colaborador tenta gravar a foto na ficha de outra pessoa
- **THEN** o backend recusa com 403

#### Scenario: Link temporário
- **WHEN** alguém guarda a URL da foto e tenta abrir depois que ela expirou
- **THEN** o Supabase recusa o acesso

### Requirement: Remoção de foto inadequada
RH e Admin SHALL poder remover a foto de qualquer colaborador, com justificativa. A remoção SHALL ficar na auditoria e SHALL avisar a pessoa.

#### Scenario: Remoção pelo RH
- **WHEN** o RH remove uma foto com a justificativa "Imagem não é do colaborador"
- **THEN** a pessoa passa a aparecer com as iniciais, recebe o aviso com a justificativa e a auditoria registra a remoção
