## ADDED Requirements

### Requirement: Avaliações atribuídas ao Gestor no F15

O sistema SHALL oferecer ao perfil Gestor uma página por ciclo das avaliações em que o usuário
autenticado é o avaliador designado e a relação é `gestor`. SHALL permitir responder competências,
salvar notas e comentários por competência e enviar avaliações pendentes ou em andamento usando
os endpoints existentes. SHALL reutilizar a validação de preenchimento da Trajetória. O backend
SHALL continuar responsável pela autorização. Avaliações enviadas ou canceladas SHALL ficar sem edição.

#### Scenario: Avaliação atribuída
- **WHEN** o Gestor abre uma avaliação atribuída a sua conta
- **THEN** a página consulta as competências autorizadas e permite salvar respostas ou enviar

#### Scenario: Avaliação de outro avaliador
- **WHEN** um registro não pertence ao usuário autenticado como avaliador
- **THEN** a página não oferece sua manipulação e trata a recusa do backend sem gravar localmente

#### Scenario: Informação não disponível
- **WHEN** não é possível confirmar a autoavaliação ou consultar contestações com o perfil Gestor
- **THEN** a página mostra estado neutro e não infere conclusão nem contagem zero

#### Scenario: Falha parcial
- **WHEN** metadados de ciclos ou organograma falham e as atribuições estão disponíveis
- **THEN** a página mantém as avaliações com identificação disponível e informa a indisponibilidade

#### Scenario: Rascunho e envio
- **WHEN** o Gestor salva o rascunho
- **THEN** apenas notas e comentários por competência são persistidos; o comentário geral é enviado somente na finalização

#### Scenario: Contestação indisponível ao Gestor
- **WHEN** o Gestor acessa a área de contestações
- **THEN** recebe informação de indisponibilidade sem consultar endpoints exclusivos de RH/Admin nem oferecer revisão de nota
