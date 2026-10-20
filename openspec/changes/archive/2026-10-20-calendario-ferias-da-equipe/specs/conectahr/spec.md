## ADDED Requirements

### Requirement: Calendário de férias da equipe
O sistema SHALL mostrar a quem decide férias (Gestor, superior direto, RH e Admin) um calendário do mês com o nome de cada pessoa da sua equipe que está de férias aprovadas, concluídas ou em análise em cada dia, do início ao fim, e SHALL alertar quando o número de pessoas de férias no mesmo dia chega ao limite escolhido. O escopo SHALL ser o da hierarquia (RH e Admin, todos; os demais, a si mesmos e quem está abaixo deles), e a resposta SHALL trazer só nome, período, dias e situação.

#### Scenario: Gestor vê quem sai no mês
- **WHEN** o gestor abre "Férias da equipe" em dezembro
- **THEN** cada dia mostra o nome de quem da equipe está de férias, e a lista do mês traz o período e a situação de cada um

#### Scenario: Muita gente no mesmo dia
- **WHEN** num dia o número de pessoas de férias chega ao limite escolhido
- **THEN** o dia aparece destacado e a tela avisa em quantos dias isso acontece e qual é o pico

#### Scenario: Fora do escopo
- **WHEN** um colaborador sem equipe abre a tela de Férias
- **THEN** a aba da equipe não aparece, e o backend devolve só as férias dele mesmo

#### Scenario: Pedido rejeitado
- **WHEN** um pedido da equipe foi rejeitado ou cancelado
- **THEN** ele não aparece no calendário da equipe
