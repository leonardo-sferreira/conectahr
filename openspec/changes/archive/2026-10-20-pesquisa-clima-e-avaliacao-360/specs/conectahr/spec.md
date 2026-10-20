## ADDED Requirements

### Requirement: Pesquisa de clima respondida de uma vez, com escala de recomendação e comentário anônimo
O sistema SHALL permitir que qualquer pessoa com ficha não desligada responda uma pesquisa de clima aberta enviando todas as notas numa única chamada, cada uma na escala da pergunta (concordância de 1 a 5 ou recomendação de 0 a 10), com um comentário opcional. As notas SHALL continuar só somando nos contadores anônimos por pergunta, departamento e nota, e o comentário SHALL ser guardado sem pessoa, departamento nem data. O envio SHALL ser tudo ou nada e SHALL ser recusado quando faltar a nota de alguma pergunta ainda não respondida.

#### Scenario: Envio completo
- **WHEN** a pessoa envia as notas de todas as perguntas da pesquisa aberta, incluindo 0 na pergunta de recomendação, e um comentário
- **THEN** cada nota soma no contador do seu departamento, a participação fica registrada e o comentário fica guardado sem autor

#### Scenario: Falta uma nota
- **WHEN** a pessoa envia as notas sem a de uma pergunta que ainda não respondeu
- **THEN** o backend recusa e nada é gravado

#### Scenario: Já respondida
- **WHEN** a pessoa tenta responder de novo uma pesquisa em que já respondeu todas as perguntas
- **THEN** o backend recusa com "Você já respondeu esta pesquisa"

### Requirement: Resultados de clima com favoráveis e comentários protegidos
Os resultados de uma pesquisa encerrada SHALL trazer, para o geral e para cada departamento que atinja o mínimo de respostas, a média e quantas respostas foram favoráveis e desfavoráveis na escala da pergunta. Os comentários SHALL aparecer só quando o número de pessoas que responderam atingir o mínimo da pesquisa, em ordem alfabética e sem identificador.

#### Scenario: Comentários abaixo do mínimo
- **WHEN** o RH consulta os resultados de uma pesquisa encerrada em que responderam menos pessoas que o mínimo
- **THEN** a resposta não traz nenhum comentário

### Requirement: Perguntas de clima só antes da abertura
O RH SHALL poder criar a pesquisa já com as perguntas numa única chamada. Incluir perguntas SHALL ser permitido só antes da data de início da pesquisa.

#### Scenario: Incluir pergunta com a pesquisa aberta
- **WHEN** o RH tenta incluir uma pergunta numa pesquisa que já começou
- **THEN** o backend recusa

### Requirement: Atribuição em lote das avaliações de desempenho
O RH SHALL poder atribuir, num ciclo de avaliação em andamento e numa única chamada, a autoavaliação e/ou a avaliação do gestor de todas as pessoas não desligadas com conta, de um departamento ou de todos. O gestor SHALL ser o superior direto e, sem ele, o gestor do departamento; ninguém SHALL avaliar a si mesmo como gestor. Avaliações que já existam no ciclo SHALL ser puladas, e cada avaliador SHALL receber um aviso.

#### Scenario: Lote repetido
- **WHEN** o RH atribui o mesmo lote duas vezes no mesmo ciclo
- **THEN** a segunda vez não cria nenhuma avaliação e informa quantas já existiam

#### Scenario: Ciclo fora de andamento
- **WHEN** o RH tenta atribuir avaliações num ciclo em planejamento
- **THEN** o backend recusa

### Requirement: Encerramento do ciclo de avaliação cancela o que ficou em aberto
Ao concluir ou cancelar um ciclo de avaliação, as avaliações ainda pendentes ou em andamento SHALL ficar canceladas.

#### Scenario: Concluir com avaliações pendentes
- **WHEN** o RH conclui um ciclo em fechamento com duas avaliações pendentes
- **THEN** as duas ficam canceladas e a resposta informa a quantidade
