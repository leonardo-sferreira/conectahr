## ADDED Requirements

### Requirement: Ciclo anual de metas
O sistema SHALL manter um ciclo de metas por ano, criado pelo RH ou pelo Admin, com três etapas em janelas de datas iguais para toda a empresa: definir as metas, registrar o que foi alcançado e fechar. Toda pessoa com ficha de colaborador, qualquer que seja o perfil, SHALL poder preencher o próprio formulário, com uma resposta por pergunta pré-definida mantida pelo RH. Na etapa 1 a pessoa SHALL escrever a meta de cada pergunta; nas etapas 2 e 3 SHALL escrever o que foi alcançado e se autoavaliar como abaixo, dentro ou acima do esperado. A pessoa SHALL poder salvar e alterar as respostas só enquanto a janela da etapa estiver aberta e a etapa não tiver sido enviada; depois do envio ou do fim da janela, as respostas SHALL ficar imutáveis. O superior direto ou o gestor do departamento da pessoa SHALL poder registrar feedback em cada etapa enviada, e o formulário, as respostas e os feedbacks SHALL ficar visíveis para a própria pessoa, para quem pode dar o feedback e para o RH e o Admin, em ciclos em andamento e encerrados. Criação e alteração de ciclo, gravação, envio e feedback SHALL ser auditados.

#### Scenario: Etapa aberta
- **WHEN** hoje está entre o início e o fim da etapa 1 e a pessoa ainda não a enviou
- **THEN** ela escreve e salva a meta de cada pergunta, e pode alterá-las até enviar

#### Scenario: Envio fecha a etapa
- **WHEN** a pessoa envia a etapa 1 com todas as metas preenchidas
- **THEN** a etapa fica enviada, nenhuma resposta dela muda mais, e o superior direto é avisado

#### Scenario: Envio incompleto
- **WHEN** a pessoa tenta enviar a etapa 2 sem a autoavaliação de uma pergunta
- **THEN** o sistema recusa o envio e a etapa continua aberta

#### Scenario: Janela encerrada
- **WHEN** a pessoa tenta gravar uma resposta da etapa 1 depois do fim da janela
- **THEN** o backend recusa, mesmo que a etapa não tenha sido enviada

#### Scenario: Etapa 2 sem metas
- **WHEN** a etapa 2 está aberta e a pessoa não enviou a etapa 1
- **THEN** o backend recusa as respostas da etapa 2

#### Scenario: Qualquer perfil preenche
- **WHEN** uma pessoa com perfil RH, Admin ou Gestor e ficha de colaborador abre o ciclo
- **THEN** ela preenche o próprio formulário como qualquer outra pessoa

#### Scenario: Feedback do superior
- **WHEN** o superior direto registra um feedback na etapa 1 enviada de alguém da equipe
- **THEN** o feedback aparece na caixa da etapa para a pessoa, para o superior e para o RH, e a pessoa é avisada no sino

#### Scenario: Feedback de quem não é da equipe
- **WHEN** alguém que não é o superior direto nem o gestor do departamento tenta registrar feedback
- **THEN** o backend recusa

#### Scenario: Datas fixas depois da abertura
- **WHEN** o RH tenta alterar as datas de um ciclo cuja etapa 1 já começou
- **THEN** o backend recusa

#### Scenario: Pergunta editada depois
- **WHEN** o RH altera o texto de uma pergunta depois de alguém ter respondido
- **THEN** o formulário respondido continua mostrando o texto da pergunta da época
