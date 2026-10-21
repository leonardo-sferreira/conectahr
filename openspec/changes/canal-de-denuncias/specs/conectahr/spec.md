## ADDED Requirements

### Requirement: Canal de denúncias anônimo com acompanhamento pelo código
O sistema SHALL oferecer um canal de denúncias que funcione com e sem login e que não ligue a denúncia a nenhuma conta, colaborador ou horário. Ao enviar, a pessoa SHALL receber um protocolo e um código de acompanhamento que só aparece uma vez; o sistema SHALL guardar apenas o hash do código. Com o código, a pessoa SHALL ver a situação, o resultado, o parecer e a conversa com a comissão, e SHALL poder responder enquanto a denúncia não for concluída. A identificação SHALL ser opcional e SHALL ficar visível só para a comissão de ética.

#### Scenario: Denúncia anônima
- **WHEN** alguém envia uma denúncia sem se identificar
- **THEN** a denúncia é gravada sem conta nem horário, e a resposta traz o protocolo e o código uma única vez

#### Scenario: Código errado
- **WHEN** alguém consulta um código que não existe
- **THEN** o sistema responde que o código não foi encontrado, sem revelar nada

### Requirement: Apuração restrita à comissão de ética
Somente os membros ativos da comissão de ética SHALL ver e apurar as denúncias, qualquer que seja o perfil; ser RH ou Admin SHALL NOT dar acesso. Cada abertura de denúncia SHALL ficar na auditoria. A conclusão SHALL exigir o resultado (procedente, improcedente ou inconclusiva) e o parecer, e a denúncia concluída SHALL NOT reabrir. Só o Admin SHALL incluir e remover membros.

#### Scenario: Admin que não é membro
- **WHEN** um Admin que não é da comissão tenta abrir a fila de denúncias
- **THEN** o backend recusa

#### Scenario: Primeira mensagem da comissão
- **WHEN** um membro escreve para o denunciante numa denúncia nova
- **THEN** a denúncia passa para em apuração e o denunciante lê a mensagem pelo código
