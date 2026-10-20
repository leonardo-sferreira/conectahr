## ADDED Requirements

### Requirement: Consulta da fila de e-mails com destinatário mascarado
O sistema SHALL permitir que RH e Admin consultem a fila de e-mails de aviso (os mais recentes, com filtro de situação) e as contagens das últimas 24 horas. O destinatário SHALL sair mascarado do backend (a primeira letra e o domínio), e o texto do e-mail SHALL NOT sair.

#### Scenario: Consulta pelo Admin
- **WHEN** o Admin consulta a fila
- **THEN** cada e-mail vem com o tipo, a situação, as tentativas e o destinatário no formato `p***@empresa.com`, sem o texto

#### Scenario: Situação inválida
- **WHEN** a consulta pede uma situação que não existe
- **THEN** o backend recusa com erro de entrada

#### Scenario: Colaborador
- **WHEN** quem não é RH nem Admin consulta a fila
- **THEN** o backend recusa
