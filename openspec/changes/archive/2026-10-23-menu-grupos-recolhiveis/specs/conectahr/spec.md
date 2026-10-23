## ADDED Requirements

### Requirement: Menu lateral com grupos recolhíveis
O menu lateral SHALL mostrar os grupos RH, Equipe e Admin, conforme o perfil, como cabeçalhos clicáveis que começam fechados e abrem ou fecham independentes uns dos outros. O grupo que contém a tela aberta SHALL abrir sozinho quando a pessoa chega nela. Auditoria e Regras SHALL ficar no grupo RH, e o menu principal SHALL ser igual para todos os perfis.

#### Scenario: Admin entra no sistema
- **WHEN** um Admin abre o app
- **THEN** vê o menu principal e os cabeçalhos "RH" e "Admin" fechados, sem os itens deles

#### Scenario: Abrir dois grupos
- **WHEN** o Admin abre o grupo RH e depois o grupo Admin
- **THEN** os dois ficam abertos

#### Scenario: Chegar numa tela de grupo
- **WHEN** o RH abre a tela Treinamentos
- **THEN** o grupo RH aparece aberto, com "Treinamentos" destacado

#### Scenario: Colaborador
- **WHEN** um Colaborador sem equipe abre o app
- **THEN** o menu não tem grupo nenhum, nem Auditoria ou Regras
