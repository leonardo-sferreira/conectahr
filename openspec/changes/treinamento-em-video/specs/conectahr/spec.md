## ADDED Requirements

### Requirement: Treinamento em vídeo com conclusão depois do mínimo assistido
O RH SHALL poder ligar um vídeo do Google Drive a um treinamento, com o mínimo a assistir (de 50% a 100%, padrão 95%), e o sistema SHALL ler a duração do vídeo no Drive ao salvar. A pessoa SHALL assistir o vídeo em "Meus treinamentos", e o sistema SHALL contar só o trecho assistido sem pular, até 2x a velocidade. O backend SHALL recusar progresso mais rápido que 2x o tempo real e SHALL liberar a conclusão pela própria pessoa só quando o progresso gravado atingir o mínimo. A conclusão SHALL ter a validade do treinamento, SHALL ficar na auditoria e SHALL zerar o progresso.

#### Scenario: Concluir antes do mínimo
- **WHEN** a pessoa assistiu 62% de um vídeo que pede 95% e tenta concluir
- **THEN** o botão "Concluir treinamento" está travado e o backend recusa a conclusão

#### Scenario: Pular para o fim do vídeo
- **WHEN** a pessoa arrasta o vídeo para o fim sem assistir
- **THEN** o player volta para o ponto mais longe já assistido e o progresso não aumenta

#### Scenario: Progresso forjado
- **WHEN** uma chamada diz que a pessoa assistiu 5 minutos a mais 30 segundos depois da última
- **THEN** o backend recusa e mantém o progresso anterior

#### Scenario: Concluir depois de assistir
- **WHEN** a pessoa assistiu 95% de um treinamento anual e clica em "Concluir treinamento" em 21/10/2026
- **THEN** a conclusão fica registrada com validade até 21/10/2027 e o progresso volta a zero
