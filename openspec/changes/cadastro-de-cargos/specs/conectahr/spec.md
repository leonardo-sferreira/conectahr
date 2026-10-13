## ADDED Requirements

### Requirement: Cadastro de cargos pelo RH
O sistema SHALL permitir que RH e Admin cadastrem e editem os cargos da empresa com nome, senioridade (Júnior, Pleno, Sênior, Especialista ou nenhuma), departamento (opcional), nível hierárquico (opcional), salário base e descrição. O nome do cargo SHALL ser o título completo que vai para a carteira de trabalho, incluindo a senioridade quando houver (ex.: "Desenvolvedor Front-end Pleno"), e SHALL ser único. A tela SHALL mostrar o nome que vai para a carteira antes de salvar. Só RH e Admin SHALL poder cadastrar ou editar cargos, e cada ação SHALL ser auditada. Na admissão, o cargo SHALL ser escolhido entre os ativos do departamento escolhido e os que não têm departamento.

#### Scenario: RH cadastra as senioridades de um cargo
- **WHEN** o RH cadastra "Desenvolvedor Front-end" como Júnior, Pleno e Sênior no departamento de TI
- **THEN** o sistema grava três cargos, "Desenvolvedor Front-end Júnior", "Desenvolvedor Front-end Pleno" e "Desenvolvedor Front-end Sênior", e os três aparecem na admissão de alguém de TI

#### Scenario: Cargo com o mesmo nome
- **WHEN** o RH tenta cadastrar um cargo com o nome de um cargo que já existe
- **THEN** o sistema recusa com mensagem clara e não grava nada

#### Scenario: Colaborador tenta cadastrar cargo
- **WHEN** um Colaborador ou Gestor tenta cadastrar ou editar um cargo
- **THEN** o sistema recusa com permissão negada
