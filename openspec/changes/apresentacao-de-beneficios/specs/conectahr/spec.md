## ADDED Requirements

### Requirement: Apresentação dos benefícios
O colaborador SHALL ver na tela Benefícios o número de benefícios ativos e, para cada um, um item que abre com a descrição, os links úteis e os materiais cadastrados pelo RH, sem valores nem descontos. RH e Admin SHALL poder editar a apresentação de cada benefício (descrição, até 10 links https e materiais PDF, JPG ou PNG de até 10 MB). Os materiais SHALL ficar em armazenamento privado e abrir por link assinado de 5 minutos, só para quem tem o benefício ativo, para o RH e para o Admin, com cada abertura auditada.

#### Scenario: Colaborador abre o material do plano de saúde
- **WHEN** o colaborador com o plano de saúde ativo abre o item do benefício e clica em "Abrir" no guia do plano
- **THEN** o sistema gera um link que vale 5 minutos e registra a abertura na auditoria

#### Scenario: Material de benefício que a pessoa não tem
- **WHEN** um colaborador pede o material de um benefício que ele não tem ativo
- **THEN** o sistema recusa com permissão negada

#### Scenario: RH cadastra um link sem https
- **WHEN** o RH salva um link que não começa com https://
- **THEN** o sistema recusa com mensagem clara e não grava nada
