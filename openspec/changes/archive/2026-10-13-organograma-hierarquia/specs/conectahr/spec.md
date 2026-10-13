## MODIFIED Requirements

### Requirement: Organograma da empresa
O sistema SHALL apresentar o organograma a qualquer usuário autenticado, de qualquer perfil, montado pelo vínculo de superior direto (`colaborador.superior_colaborador_id`): quem não tem superior direto (ou cujo superior não está mais no organograma) fica no topo, e abaixo de cada pessoa ficam as pessoas que a têm como superior direto. O organograma SHALL incluir todo colaborador cujo status não seja `Desligado`, inclusive quem estiver de férias ou afastado. Cada pessoa SHALL aparecer com nome, cargo, nível do cargo e departamento, e nenhum outro dado (sem e-mail, CPF, salário ou dado de contato). A pessoa SHALL poder navegar: escolher alguém e ver o superior dessa pessoa e quem está abaixo dela, seguir o caminho até o topo, voltar à própria posição, buscar por nome ou cargo e filtrar por departamento. Dentro de um mesmo superior, as pessoas SHALL aparecer pela ordem do nível do cargo e depois pelo nome; cargo sem nível vem depois dos que têm nível.

#### Scenario: Consulta do organograma
- **WHEN** um usuário autenticado de qualquer perfil abre o organograma
- **THEN** o sistema mostra a posição dele, o caminho até o topo e quem está abaixo dele, com nome, cargo, nível e departamento de cada pessoa

#### Scenario: Navegar pela hierarquia
- **WHEN** a pessoa clica no topo do organograma (ex.: a pessoa sem superior direto)
- **THEN** o sistema mostra quem tem essa pessoa como superior direto, e clicar em qualquer um deles desce mais um nível

#### Scenario: Colaborador de ferias no organograma
- **WHEN** um colaborador está com status `Ferias` ou `Afastado`
- **THEN** ele continua aparecendo no organograma; somente colaboradores `Desligado` são omitidos

## ADDED Requirements

### Requirement: Niveis hierarquicos da empresa
O sistema SHALL permitir que RH e Admin mantenham os níveis hierárquicos da empresa (nome e ordem, do topo para a base: por exemplo CEO, Diretoria, Head, Gerência, Coordenação, Supervisão, Analista, Operador, Estagiário), sem uma lista fixa no código. Cada cargo SHALL poder ter um nível. A inclusão, a edição (nome e ordem), a desativação de um nível e a troca do nível de um cargo SHALL ser auditadas, e só RH e Admin SHALL poder fazê-las. Um nível desativado SHALL deixar de rotular os cargos no organograma, sem apagar o vínculo.

#### Scenario: RH cadastra a hierarquia
- **WHEN** o RH cadastra os níveis "Diretoria" (ordem 1) e "Coordenação" (ordem 2) e liga cada cargo ao seu nível
- **THEN** o organograma mostra o nível de cada pessoa e ordena as pessoas de um mesmo superior por esse nível

#### Scenario: Colaborador tenta mudar a hierarquia
- **WHEN** um Colaborador ou Gestor tenta incluir um nível ou mudar o nível de um cargo
- **THEN** o sistema recusa com permissão negada e não grava nada
