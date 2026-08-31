## Purpose

Define o comportamento da gestão de vagas e candidaturas do ConectaRH: o cadastro de vagas pelo RH, a candidatura de colaboradores já autenticados, a submissão e o acompanhamento de candidaturas por candidatos externos sem conta no sistema, e a API (pública e de autorização) que o **ConectaRH Vagas** — site separado, fora do escopo desta mudança — irá consumir para exibir vagas, receber candidaturas e servir de área de gestão para o RH.

## ADDED Requirements

### Requirement: Cadastro e ciclo de vida de vaga
O sistema SHALL permitir que RH ou Admin cadastrem vagas com título, tipo (`interna` ou `externa`), cargo e departamento vinculados, descrição, requisitos e quantidade de posições. O estado da vaga SHALL ser `rascunho`, `aberta`, `pausada`, `encerrada` ou `cancelada`. Somente vagas `rascunho` podem ser publicadas (`rascunho -> aberta`); vagas `aberta` podem ser pausadas ou encerradas; vagas `pausada` podem ser reabertas ou encerradas; vagas `encerrada` ou `cancelada` não aceitam novas candidaturas nem retornam ao estado `aberta`.

#### Scenario: Publicar vaga
- **WHEN** RH publica uma vaga em rascunho com os campos obrigatórios preenchidos
- **THEN** o sistema muda o estado para `aberta` e a vaga passa a aceitar candidaturas

#### Scenario: Candidatura bloqueada em vaga fechada
- **WHEN** um candidato tenta se candidatar a uma vaga `pausada`, `encerrada` ou `cancelada`
- **THEN** o sistema rejeita a candidatura e informa que a vaga não está aceitando candidaturas

### Requirement: Visibilidade de vaga interna e externa
O sistema SHALL distinguir vagas `interna` (visíveis somente a colaboradores autenticados do ConectaRH) de vagas `externa` (visíveis publicamente, sem autenticação, além de para colaboradores autenticados). A API pública SHALL retornar somente vagas do tipo `externa` com estado `aberta`. A listagem para colaborador autenticado SHALL retornar todas as vagas com estado `aberta`, dos dois tipos.

#### Scenario: Vaga interna não aparece na API pública
- **WHEN** o ConectaRH Vagas consulta a lista pública de vagas abertas
- **THEN** o sistema retorna somente vagas do tipo `externa` com estado `aberta`

#### Scenario: Colaborador consulta todas as vagas abertas
- **WHEN** um colaborador autenticado consulta as vagas abertas da empresa
- **THEN** o sistema retorna as vagas com estado `aberta`, tanto `interna` quanto `externa`

### Requirement: Candidatura de colaborador autenticado
O sistema SHALL permitir que um colaborador autenticado, com status profissional `Ativo`, se candidate a qualquer vaga com estado `aberta` (`interna` ou `externa`) sem reenviar nome, e-mail ou telefone — esses dados SHALL ser obtidos do próprio cadastro do colaborador. A candidatura SHALL ser registrada com o `colaborador_id` do solicitante, e o currículo SHALL ser opcional nesse fluxo. As mesmas regras de vaga fechada e de duplicidade da candidatura de visitante externo SHALL se aplicar, com a duplicidade verificada por `colaborador_id` em vez de e-mail.

#### Scenario: Colaborador se candidata com um clique
- **WHEN** um colaborador ativo se candidata a uma vaga aberta
- **THEN** o sistema cria a candidatura vinculada ao `colaborador_id`, com estado `recebida`, usando os dados de contato já cadastrados

#### Scenario: Colaborador não pode se candidatar duas vezes
- **WHEN** um colaborador tenta se candidatar novamente à mesma vaga enquanto já possui candidatura ativa para ela
- **THEN** o sistema rejeita a nova candidatura e informa a existência da candidatura ativa

### Requirement: Autorização de RH no ConectaRH Vagas
O sistema SHALL emitir, para um usuário autenticado com perfil RH ou Admin, um token de autorização de curta duração para acessar a área de gestão do ConectaRH Vagas sem exigir um novo login. O token SHALL expirar em um curto intervalo definido no design e SHALL deixar de ser aceito após expirar ou após o primeiro uso, o que ocorrer primeiro.

#### Scenario: RH acessa a área de gestão
- **WHEN** um usuário RH ou Admin solicita acesso ao ConectaRH Vagas a partir do ConectaRH
- **THEN** o sistema emite um token de curta duração que autoriza a sessão de gestão no ConectaRH Vagas

#### Scenario: Token de handoff expirado ou reutilizado
- **WHEN** o ConectaRH Vagas tenta validar um token de handoff expirado ou já utilizado
- **THEN** o sistema recusa a autorização e exige nova solicitação a partir do ConectaRH

### Requirement: Submissão pública de candidatura
O sistema SHALL permitir que qualquer pessoa sem conta no ConectaRH (visitante externo do ConectaRH Vagas) submeta uma candidatura para uma vaga `aberta` informando nome, e-mail, telefone e currículo. O sistema SHALL rejeitar uma nova submissão do mesmo e-mail para a mesma vaga enquanto existir candidatura ativa (qualquer estado exceto `rejeitada`).

#### Scenario: Candidatura enviada com sucesso
- **WHEN** um candidato submete uma candidatura completa para uma vaga aberta
- **THEN** o sistema cria a candidatura com estado `recebida` e entrega ao candidato um identificador de acompanhamento

#### Scenario: Candidatura duplicada
- **WHEN** o mesmo e-mail tenta se candidatar novamente à mesma vaga enquanto já existe candidatura ativa
- **THEN** o sistema rejeita a nova submissão e informa que já existe uma candidatura ativa

### Requirement: Acompanhamento de candidatura sem conta
O sistema SHALL permitir que um candidato consulte o estado da própria candidatura sem possuir conta no ConectaRH, usando o identificador de acompanhamento entregue na submissão, sem expor candidaturas de outros candidatos.

#### Scenario: Consulta de status válida
- **WHEN** o candidato informa o identificador de acompanhamento correto
- **THEN** o sistema retorna o estado atual da candidatura e o histórico de mudanças de estado

#### Scenario: Identificador inválido
- **WHEN** um identificador de acompanhamento inválido ou pertencente a outra candidatura é informado
- **THEN** o sistema nega o acesso sem revelar se a candidatura existe

### Requirement: Gestão de candidaturas pelo RH
O sistema SHALL permitir que RH ou Admin listem e filtrem candidaturas por vaga e por estado, e decidam a transição de estado com responsável e data registrados. Os estados SHALL ser `recebida`, `em_triagem`, `em_entrevista`, `em_oferta`, `contratado` ou `rejeitada`, avançando nessa ordem sem pular etapas; a rejeição SHALL ser possível a partir de qualquer estado anterior a `contratado`.

#### Scenario: RH avança candidatura
- **WHEN** RH move uma candidatura de `recebida` para `em_triagem`
- **THEN** o sistema registra a transição, o responsável e a data da decisão

#### Scenario: Rejeição em qualquer etapa
- **WHEN** RH rejeita uma candidatura em `em_triagem`, `em_entrevista` ou `em_oferta`
- **THEN** o sistema muda o estado para `rejeitada` e preserva o histórico de estados anteriores

### Requirement: Proteção de dados do candidato
O sistema SHALL tratar contato e currículo do candidato como dados pessoais protegidos, armazenando o currículo em repositório privado acessível somente a RH, Admin e ao próprio candidato via identificador de acompanhamento. O sistema SHALL não criar usuário, colaborador ou qualquer acesso ao ConectaRH a partir de uma candidatura, inclusive quando o estado avança para `contratado`.

#### Scenario: Currículo não acessível publicamente
- **WHEN** alguém tenta acessar o arquivo de currículo sem ser RH, Admin ou o candidato dono da candidatura
- **THEN** o sistema nega o acesso

#### Scenario: Candidatura não cria acesso
- **WHEN** uma candidatura é criada ou movida para `contratado`
- **THEN** o sistema não cria nenhuma conta de usuário nem vincula automaticamente a um colaborador
