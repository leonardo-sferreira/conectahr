## ADDED Requirements

### Requirement: Indicadores parciais da equipe

O sistema SHALL oferecer ao Gestor o F18 parcial usando fontes autorizadas e coberturas
identificadas separadamente. SHALL mostrar a série de horas extras gravadas dos últimos seis
meses e ausências agrupadas por registro, sem férias. SHALL apresentar o banco como saldo
corrente departamental, sem atribuir-lhe recorte histórico. SHALL suprimir grupos menores que
o piso padrão de cinco pessoas. SHALL preservar indisponibilidade em falhas e falta de cobertura.

#### Scenario: Mês sem cobertura
- **WHEN** um mês falha ou não há registros válidos para todos os membros do recorte
- **THEN** seu valor de horas extras fica indisponível, sem zero inventado

#### Scenario: Banco parcialmente indisponível
- **WHEN** uma consulta individual necessária falha
- **THEN** o total do banco fica indisponível e as fontes da folha continuam independentes

#### Scenario: Fontes com escopos diferentes
- **WHEN** folha e banco permitem conjuntos diferentes
- **THEN** cada agregado usa somente seu conjunto autorizado e informa sua cobertura

#### Scenario: Métricas bloqueadas
- **WHEN** o Gestor abre a página
- **THEN** Absenteísmo e Clima ficam indisponíveis e Exportar CSV permanece desabilitado,
  sem endpoint restrito nem exportação simulada

#### Scenario: Privacidade
- **WHEN** a página recebe campos extras ou um grupo com menos de cinco pessoas
- **THEN** campos sensíveis não são apresentados e os agregados desse grupo são suprimidos
