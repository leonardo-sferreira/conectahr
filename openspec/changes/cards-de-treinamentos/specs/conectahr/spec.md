## ADDED Requirements

### Requirement: Treinamentos em cards por tipo de conteúdo
"Meus treinamentos" SHALL mostrar os treinamentos ativos do público da pessoa como cards clicáveis em grade. Cada card SHALL ter capa, nome, descrição cortada, tipo de conteúdo (vídeo, PDF ou apresentação), categoria, carga horária e situação. A tela SHALL filtrar por "Pendentes", "Em andamento" e "Concluídos" e SHALL mostrar os cards numa coluna em tela estreita. Sem capa enviada pelo RH, o card SHALL usar a miniatura do vídeo ou a ilustração da categoria.

#### Scenario: Três tipos
- **WHEN** a pessoa tem um treinamento de vídeo, um de PDF e um de apresentação
- **THEN** os três aparecem como cards, cada um com a capa e o tipo indicado

#### Scenario: Abrir e voltar
- **WHEN** a pessoa abre um card no filtro "Em andamento" e depois clica em "Voltar"
- **THEN** ela vê o detalhe com o conteúdo e, ao voltar, o filtro "Em andamento" continua escolhido

#### Scenario: Lista vazia
- **WHEN** a pessoa não tem nenhum treinamento
- **THEN** a tela mostra o estado vazio do Figma

### Requirement: Conclusão por tipo de conteúdo
O backend SHALL liberar a conclusão de um treinamento de PDF ou apresentação só depois que a pessoa abriu o conteúdo e confirmou "Li e compreendi o conteúdo", e SHALL gravar a conclusão com a validade do treinamento e a auditoria. O treinamento de vídeo SHALL continuar exigindo o mínimo assistido.

#### Scenario: PDF sem abrir
- **WHEN** a pessoa tenta concluir um treinamento de PDF sem ter aberto o conteúdo
- **THEN** o backend recusa a conclusão

#### Scenario: PDF lido
- **WHEN** a pessoa abre o PDF, marca "Li e compreendi o conteúdo" e conclui
- **THEN** a conclusão fica registrada com a validade do treinamento e aparece em "Concluídos"
