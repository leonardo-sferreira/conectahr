## ADDED Requirements

### Requirement: Cadastro de competências de avaliação

RH e Admin SHALL poder cadastrar, editar e desativar as competências de avaliação, com nível e situação (ativa ou inativa). O formulário de uma avaliação SHALL mostrar as competências ativas do nível do avaliado ou, se o nível não tiver nenhuma, todas as ativas. Gestor e Colaborador SHALL NOT cadastrar competências.

#### Scenario: Avaliação com formulário preenchível
- **WHEN** existe pelo menos uma competência ativa e o RH atribui uma avaliação a um Gestor
- **THEN** o Gestor vê as competências no formulário, salva o rascunho e envia a avaliação

#### Scenario: Cadastro restrito
- **WHEN** um Gestor ou Colaborador tenta cadastrar uma competência
- **THEN** o backend recusa com 403 e nada é gravado

### Requirement: Indicadores agregados do setor do Gestor

O backend SHALL devolver ao Gestor só números agregados do setor que ele gerencia, nos últimos 6 meses: horas extras, ausências, absenteísmo, saldo do banco de horas e clima, sem nomes nem identificadores de pessoas. Setor com menos de 5 pessoas SHALL ter os números ocultados, e o clima SHALL seguir o mínimo de respostas da pesquisa. A exportação SHALL ser auditada. A folha individual SHALL NOT ter o escopo ampliado.

#### Scenario: Setor pequeno
- **WHEN** o setor do Gestor tem menos de 5 pessoas
- **THEN** os indicadores voltam vazios, com o motivo, e nenhum número individual pode ser deduzido

#### Scenario: Exportar
- **WHEN** o Gestor exporta os indicadores
- **THEN** a exportação fica na auditoria, com o setor e o período, sem dados de pessoas

### Requirement: Delegação do Gestor só no que ele decide

O Gestor SHALL criar delegação só nos escopos férias, correção de ponto e todas, escolhendo o substituto num catálogo de pessoas ativas do próprio setor e de outros Gestores. A delegação SHALL valer quando o titular é quem decidiria o pedido (o superior direto e, sem ele, o gestor do departamento). Durante a delegação, a Central do substituto SHALL mostrar os pedidos que o titular decidiria.

#### Scenario: Escopo do RH
- **WHEN** o Gestor tenta delegar desligamento ou solicitação ao RH
- **THEN** o backend recusa com 400

#### Scenario: Substituto fora do catálogo
- **WHEN** o Gestor indica um substituto que não é do setor nem Gestor
- **THEN** o backend recusa com 400

### Requirement: Contestação respondida pelo Gestor

O avaliador de uma avaliação de relação gestor SHALL responder a contestação mantendo a nota ou revisando-a (de 1 a 5), com justificativa. A nota revisada SHALL passar a valer, guardando a original. O RH SHALL ter a palavra final, podendo definir a nota ao fechar a contestação.

#### Scenario: Gestor revisa a nota
- **WHEN** o Gestor revisa a nota de uma avaliação contestada de 2 para 3
- **THEN** a avaliação passa a ter nota 3, a nota original 2 fica guardada e a contestação continua aberta para o RH

#### Scenario: Outro usuário tenta responder
- **WHEN** quem não é o avaliador da avaliação tenta responder como Gestor
- **THEN** o backend recusa com 403

### Requirement: Prazo e autoavaliação para o Gestor

Na avaliação de relação gestor, o backend SHALL informar o prazo (a data de fim do ciclo) e a situação da autoavaliação da pessoa no mesmo ciclo, sem as notas nem os comentários dela.

#### Scenario: Autoavaliação enviada
- **WHEN** a pessoa já enviou a autoavaliação do ciclo
- **THEN** o Gestor vê "Autoavaliação enviada" na avaliação dele, sem ver as notas
