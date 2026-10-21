## ADDED Requirements

### Requirement: Avaliação de riscos psicossociais anônima por setor
O sistema SHALL permitir que o RH abra uma avaliação de riscos psicossociais com o questionário padrão, por dimensão e respondida por frequência, usando o mesmo anonimato da pesquisa de clima: sem resposta individual, resultados só depois do encerramento e só para setores com o mínimo de respostas. O resultado SHALL mostrar o nível de risco (baixo, moderado ou alto) por dimensão e setor, e a participação por setor.

#### Scenario: Setor abaixo do mínimo
- **WHEN** um setor teve menos respostas que o mínimo da avaliação
- **THEN** o mapa de risco não mostra esse setor, e a empresa continua aparecendo

### Requirement: Plano de ação e relatório para o PGR
O RH SHALL registrar ações para os riscos (setor, dimensão, medida, responsável, prazo e situação), e cada criação ou atualização SHALL ficar na auditoria. A tela SHALL destacar os riscos altos sem ação e as ações atrasadas, e SHALL gerar um relatório com a participação, o inventário de riscos e o plano de ação.

#### Scenario: Risco alto sem ação
- **WHEN** uma dimensão de um setor tem risco alto e nenhuma ação não cancelada no plano
- **THEN** ela aparece em "Riscos altos sem ação", com "Criar ação" já preenchido

#### Scenario: Ação em avaliação que não é psicossocial
- **WHEN** alguém tenta criar uma ação para uma pesquisa de clima comum
- **THEN** o backend recusa
