## ADDED Requirements

### Requirement: Consulta parcial de delegações pelo Gestor

O sistema SHALL oferecer ao Gestor uma página com suas delegações como titular ou substituto,
usando somente os contratos existentes. SHALL distinguir a direção e separar Ativas e futuras
de Encerradas. SHALL derivar Agendada, Ativa e Encerrada pelas datas UTC e dar precedência ao
cancelamento. SHALL mostrar vigência indisponível se os dados não permitirem classificá-la.
SHALL apresentar período, escopo, situação e motivo, sem expor IDs ou dados sensíveis.

#### Scenario: Delegação recebida
- **WHEN** o usuário é substituto de uma delegação retornada
- **THEN** vê Recebida por mim, titular não disponível quando não há nome autorizado, e nenhuma ação de cancelamento

#### Scenario: Cancelar uma delegação concedida
- **WHEN** o titular cancela uma delegação ainda não cancelada e o backend confirma
- **THEN** a lista é atualizada, a delegação aparece Cancelada em Encerradas e a página mostra sucesso

#### Scenario: Cancelamento recusado ou falha parcial
- **WHEN** a consulta ou o cancelamento falha
- **THEN** a página informa a falha sem transformar indisponibilidade em vazio nem simular cancelamento

#### Scenario: Criação bloqueada
- **WHEN** o Gestor abre Nova delegação sem catálogo autorizado de substitutos
- **THEN** a criação permanece indisponível, sem pedir IDs nem chamar POST delegacoes

#### Scenario: Limitação operacional
- **WHEN** a página apresenta escopos e orientações
- **THEN** informa a integração parcial e a ausência de encaminhamento à Central, sem ampliar permissões nem afirmar transferência de todos os poderes
