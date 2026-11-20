## ADDED Requirements

### Requirement: Cadastro de competências de avaliação

RH e Admin SHALL poder cadastrar, editar e desativar as competências de avaliação, com nível e situação (ativa ou inativa). O formulário de uma avaliação SHALL mostrar as competências ativas do nível do avaliado ou, se o nível não tiver nenhuma, todas as ativas. Gestor e Colaborador SHALL NOT cadastrar competências.

#### Scenario: Avaliação com formulário preenchível
- **WHEN** existe pelo menos uma competência ativa e o RH atribui uma avaliação a um Gestor
- **THEN** o Gestor vê as competências no formulário, salva o rascunho e envia a avaliação

#### Scenario: Cadastro restrito
- **WHEN** um Gestor ou Colaborador tenta cadastrar uma competência
- **THEN** o backend recusa com 403 e nada é gravado
