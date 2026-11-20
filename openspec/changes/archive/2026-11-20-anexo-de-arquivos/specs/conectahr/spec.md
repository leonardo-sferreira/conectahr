## ADDED Requirements

### Requirement: Anexo de arquivo em Documentos
O sistema SHALL permitir que a pessoa envie um documento anexando o arquivo (PDF, JPG ou PNG, até 10 MB), sem informar link. O arquivo SHALL ser guardado num armazenamento privado, com nome aleatório e sem dado pessoal no caminho. A chave do armazenamento SHALL ficar só no backend. O endereço de envio SHALL ser gerado pelo backend só para quem pode cadastrar o documento (o próprio colaborador ativo, o RH ou o Admin), e a geração SHALL ser auditada. Ao abrir o arquivo, o backend SHALL devolver um link assinado que vale 5 minutos, só ao dono, ao RH e ao Admin, e SHALL auditar cada abertura.

#### Scenario: Colaborador anexa a foto do RG
- **WHEN** o colaborador escolhe o tipo RG, anexa uma foto JPG de 2 MB e clica em "Enviar para o RH"
- **THEN** o arquivo é guardado no armazenamento privado, o documento fica "Em análise" e o RH é avisado

#### Scenario: Arquivo de tipo ou tamanho não aceito
- **WHEN** a pessoa anexa um arquivo de 15 MB ou um arquivo .zip
- **THEN** a tela recusa com a mensagem do motivo e nada é enviado

#### Scenario: RH abre o arquivo anexado
- **WHEN** o RH clica em "Ver" num documento anexado
- **THEN** o backend devolve um link que vale 5 minutos e registra a abertura na auditoria

#### Scenario: Outra pessoa tenta abrir
- **WHEN** um Gestor ou outro colaborador pede o arquivo de um documento que não é dele
- **THEN** o backend recusa com permissão negada e não gera link

#### Scenario: Armazenamento não configurado
- **WHEN** as variáveis do Supabase não estão definidas no Xano
- **THEN** o envio falha com mensagem clara e nenhum documento é gravado
