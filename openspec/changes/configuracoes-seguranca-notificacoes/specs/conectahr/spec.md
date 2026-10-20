## ADDED Requirements

### Requirement: Segurança da conta em Configurações
O sistema SHALL permitir que a pessoa troque a própria senha informando a senha atual, e SHALL encerrar as outras sessões ativas dela quando a senha for trocada, mantendo a sessão de onde a troca foi feita. O sistema SHALL mostrar as sessões ativas da pessoa, indicando qual é a do aparelho atual, e SHALL permitir encerrar qualquer outra, uma a uma ou todas de uma vez.

#### Scenario: Troca de senha encerra as outras sessões
- **WHEN** a pessoa troca a senha com a senha atual correta, estando conectada em dois aparelhos
- **THEN** a senha muda, a sessão do aparelho de onde trocou continua e a do outro aparelho é encerrada

#### Scenario: Senha atual errada
- **WHEN** a pessoa informa a senha atual errada
- **THEN** a senha não muda e nenhuma sessão é encerrada

#### Scenario: Este dispositivo
- **WHEN** a pessoa abre Sessões e dispositivos
- **THEN** a sessão do aparelho atual aparece marcada como "Este dispositivo", sem a opção de encerrar

### Requirement: Preferências de aviso por assunto e canal
O sistema SHALL permitir que a pessoa ligue ou desligue, por assunto (férias e ausências, ponto e correções, documentos, avaliações e metas, solicitações ao RH), os avisos na plataforma e por e-mail, e SHALL respeitar essa escolha ao criar avisos e ao pôr e-mails na fila. Avisos de benefícios, alertas de segurança e pedidos que esperam a decisão da pessoa SHALL ser sempre entregues. Sem escolha registrada, todos os canais SHALL estar ligados.

#### Scenario: Plataforma desligada
- **WHEN** a pessoa desliga "Na plataforma" em Férias e ausências e o gestor aprova as férias dela
- **THEN** nenhum aviso aparece no sino dela sobre essa aprovação

#### Scenario: E-mail desligado
- **WHEN** a pessoa desliga o e-mail de Solicitações ao RH e o RH responde a solicitação dela
- **THEN** o aviso aparece no sino, mas nenhum e-mail vai para a fila

#### Scenario: Pedido para decidir
- **WHEN** a pessoa, sendo gestora, desligou "Na plataforma" em Férias e ausências e alguém da equipe pede férias
- **THEN** o aviso do pedido novo aparece mesmo assim

#### Scenario: Assunto obrigatório
- **WHEN** alguém tenta desligar alertas de segurança ou benefícios
- **THEN** o backend recusa
