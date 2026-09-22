# Domain Model — ConectaRH

Este documento descreve os conceitos fundamentais do domínio do ConectaRH e seus
relacionamentos — não é um dicionário de dados. Para os campos exatos de cada tabela, ver
`xano-workspace/table/*.xs`; para o comportamento (validações, máquinas de estado, autorização,
auditoria) de cada entidade, ver `docs/regras-de-negocio.md`.

## Visão geral

```
Colaborador (vinculado a User)
│
├── Cargo ── Departamento ── (gestor: Colaborador)
│
├── HistoricoProfissional (snapshot por período)
│
├── RegistroPonto ── CorrecaoPonto
│   └── BancoHorasLancamento
│
├── Documento ── PendenciaDocumento
│   └── EventoSST
│
├── Ferias
├── Ausencia
├── SolicitacaoDesligamento
│
├── Avaliacao (CicloAvaliacao, CompetenciaAvaliacao) ── ContestacaoAvaliacao
├── MetaAvaliacao ── MetaCheckin
├── Pdi
├── Reconhecimento
├── RespostaClimaParticipacao (PesquisaClima / PerguntaClima / RespostaClima anônima)
│
├── SolicitacaoRH
└── Onboarding ── OnboardingItem

InstrumentoNormativo ── RegraOverride ── RegraContrato ── RegraAplicada
DelegacaoAprovacao (titular User → substituto User, por escopo)
Auditoria (registra ações sobre as entidades acima)

Comunicado, ArtigoFaq, Feriado, ParametroProtegido — catálogos/conteúdo transversal
```

## 1. Identidade e acesso

### User

Conta de acesso ao sistema. Um `user` tem exatamente um `perfil` (Admin, RH, Gestor,
Colaborador) e pode estar vinculado a um `Colaborador`.

- **Atributos-chave:** email (único), senha, perfil, ativo, senha de primeiro acesso
  obrigatória.
- **Relacionamentos:** um User tem no máximo um Colaborador associado (`colaborador.user_id`);
  um User tem várias Sessao; um User pode ser titular ou substituto em várias
  DelegacaoAprovacao.
- **Regras estruturais:** login exige validação adicional por código de acesso (OTP) de 6
  dígitos enviado por e-mail antes de emitir o token de sessão.

### Sessao

Registro de uma sessão autenticada de um User (token válido por 1 hora).

- **Relacionamentos:** pertence a um User.
- **Regras estruturais:** pode ser encerrada individualmente pelo dono ou em massa
  ("encerrar outras"); é uma aproximação de "sessão atual" — o token em si permanece válido
  até expirar mesmo que a sessão seja marcada encerrada.

## 2. Colaboradores e estrutura organizacional

### Colaborador

Representa a pessoa com vínculo profissional na empresa — o centro do domínio, ao qual quase
toda outra entidade se relaciona.

- **Atributos-chave:** nome, CPF (único), dados pessoais e de endereço, dados bancários
  (visíveis só a ele e ao RH), cargo, departamento, nível (l1-l5), tipo de contrato
  (CLT/PJ/Estágio/Aprendiz/Temporário/Outro), status (Ativo/Ferias/Afastado/Desligado).
- **Relacionamentos:** pertence a um Cargo e a um Departamento; tem uma sequência de
  HistoricoProfissional; é dono de seus RegistroPonto, Documento, Ferias, Ausencia,
  Avaliacao, MetaAvaliacao, Pdi etc.
- **Regras estruturais:** o tipo de contrato determina regras operacionais distintas (jornada,
  banco de horas, férias) — o cadastro por si só não presume vínculo ou direitos de empregado.

### Cargo / Departamento

Catálogos organizacionais.

- **Departamento** tem um `gestor_colaborador_id` opcional — o Colaborador responsável por
  aprovar ações da equipe daquele departamento (correção de ponto, desligamento etc.).
- **Regras estruturais:** o vínculo gestor-departamento também tem histórico
  (`HistoricoGestorDepartamento`), com um único gestor vigente por vez.

### HistoricoProfissional

Snapshot append-only do vínculo profissional do colaborador ao longo do tempo (cargo,
departamento, nível, salário, tipo de contrato, tipo de alteração — admissão, promoção,
alteração de departamento/salário/cargo/contrato, desligamento).

- **Relacionamentos:** pertence a um Colaborador.
- **Regras estruturais:** cada alteração de vínculo encerra o registro aberto (`data_fim`) e
  cria um novo; o primeiro registro de um colaborador é sempre do tipo "admissão".

## 3. Jornada e banco de horas

### RegistroPonto

Um registro por colaborador por dia, com as quatro marcações (entrada, início/fim de
intervalo, saída).

- **Relacionamentos:** pertence a um Colaborador; pode ter uma ou mais CorrecaoPonto.
- **Regras estruturais:** marcações seguem ordem estrita; horas trabalhadas são calculadas a
  partir das marcações.

### CorrecaoPonto

Solicitação de ajuste em um campo específico de um RegistroPonto.

- **Relacionamentos:** pertence a um RegistroPonto e a um Colaborador (o solicitante).
- **Regras estruturais:** decidida por RH/Admin ou pelo Gestor do departamento do colaborador;
  aprovação aplica o valor solicitado e recalcula horas quando as quatro marcações existem.

### BancoHorasLancamento

Lançamento append-only de crédito ou débito de horas.

- **Relacionamentos:** pertence a um Colaborador; pode referenciar um InstrumentoNormativo de
  origem.
- **Regras estruturais:** imutável desde a criação; o saldo nunca é armazenado, é sempre
  recalculado somando os lançamentos; só existe para contratos cuja RegraContrato permite banco
  de horas.

## 4. Documentos

### Documento

Arquivo enviado pelo colaborador (ou pelo RH, no caso de holerite/informe de rendimentos) para
análise e aprovação.

- **Atributos-chave:** tipo (RG, CPF, CTPS, ASO, holerite, informe de rendimentos, entre
  outros), status (pendente_analise → aprovado/rejeitado → vencido/substituido → arquivado).
- **Relacionamentos:** pertence a um Colaborador; pode referenciar o Documento que substitui.
- **Regras estruturais:** exclusão física é bloqueada para todos os perfis — o ciclo de vida
  termina em arquivamento; holerite/informe de rendimentos só podem ser anexados pelo RH e não
  vencem.

### PendenciaDocumento

Solicitação do RH para que o colaborador envie um documento de um tipo específico.

- **Relacionamentos:** pertence a um Colaborador; é atendida automaticamente quando um
  Documento do tipo pedido é cadastrado.

### EventoSST

Registro operacional de exame ocupacional (ASO) — deliberadamente sem campo de diagnóstico ou
registro clínico livre.

- **Relacionamentos:** pertence a um Colaborador.

## 5. Férias, ausências e desligamento

### Ferias

Solicitação de período de férias de um colaborador.

- **Relacionamentos:** pertence a um Colaborador.
- **Regras estruturais:** ciclo `Pendente → Aprovada/Rejeitada/Cancelada`; verificação de
  conflito (antecedência, período aquisitivo, sobreposição com férias/ausências do próprio
  colaborador, colegas do mesmo departamento no período) é informativa, não bloqueia a decisão.

### Ausencia

Registro de falta, atestado, afastamento ou licença.

- **Relacionamentos:** pertence a um Colaborador.
- **Regras estruturais:** ciclo `Pendente → Aprovada/Rejeitada`, e `Aprovada → Registrado`;
  exclusão física é bloqueada para todos os perfis.

### SolicitacaoDesligamento

Pedido de desligamento de um colaborador, iniciado pelo próprio colaborador ou pelo gestor.

- **Relacionamentos:** referencia o Colaborador alvo e o solicitante (User).
- **Regras estruturais:** `pendente → em_analise → aprovada/rejeitada`; aprovação de
  desligamento imediato desliga o colaborador na mesma transação (desativa acesso, encerra
  histórico profissional); aviso prévio agenda a data efetiva. Decisão é exclusiva do RH.

## 6. Regras contratuais e instrumentos normativos

### InstrumentoNormativo

Documento formal que fundamenta uma regra (norma legal, acordo/convenção coletiva, termo
aditivo, decisão judicial, regime especial).

- **Relacionamentos:** pode ter vários RegraOverride associados.
- **Regras estruturais:** ciclo `rascunho → pendente_aprovacao → vigente` (ou rejeitado,
  suspenso, revogado); instrumentos coletivos exigem número de solicitação Mediador, registro
  MTE e processo MTE antes de ficarem vigentes; autoaprovação é bloqueada.

### RegraOverride

Sobrescrita de um parâmetro protegido (ex.: dias de férias, horas diárias) para um escopo
específico (empresa, departamento, cargo, tipo de contrato, colaborador etc.), fundamentada em
um InstrumentoNormativo.

- **Relacionamentos:** pertence a um InstrumentoNormativo.
- **Regras estruturais:** bloqueada quando o ParametroProtegido correspondente tem
  `nivel_protecao = sem_override`; nova aprovação encerra a versão vigente anterior do mesmo
  parâmetro+escopo e cria uma nova versão — nunca edita a regra anterior como registro ativo.

### RegraContrato / RegraAplicada

Parâmetros-base por tipo de contrato e registro de qual regra foi aplicada a um processo.
Tabelas existentes no domínio, mas ainda sem endpoint de API que as consuma — o motor de
resolução de regras (aplicar override + regra de contrato) é trabalho futuro do MVP.

### ParametroProtegido

Catálogo dos parâmetros que podem (ou não) ser sobrescritos por RegraOverride, com o nível de
proteção de cada um.

## 7. Avaliação e desenvolvimento

### CicloAvaliacao

Período de avaliação de desempenho (planejamento → em andamento → fechamento → concluído).

- **Relacionamentos:** agrupa várias Avaliacao, MetaAvaliacao e Pdi do mesmo período.

### Avaliacao

Avaliação de um colaborador por um avaliador, em uma relação específica (autoavaliação, gestor,
par, subordinado, RH), com respostas por competência.

- **Relacionamentos:** pertence a um CicloAvaliacao; tem várias RespostaAvaliacao (uma por
  CompetenciaAvaliacao); pode ter uma ContestacaoAvaliacao.
- **Regras estruturais:** `pendente → em_andamento → enviada` (terminal); nota geral é a média
  das respostas; só o avaliado pode contestar, só depois de enviada.

### MetaAvaliacao / MetaCheckin

Meta individual de um colaborador em um ciclo, com trilha de check-ins append-only.

- **Relacionamentos:** MetaCheckin pertence a uma MetaAvaliacao.
- **Regras estruturais:** `planejada → em_andamento → concluida`; a meta guarda só o
  check-in mais recente, a trilha completa fica em MetaCheckin.

### Pdi

Plano de desenvolvimento individual do colaborador.

- **Regras estruturais:** progresso ≥ 100% conclui automaticamente.

### Reconhecimento

Mensagem de reconhecimento entre colaboradores.

- **Regras estruturais:** visibilidade não é escolhida pelo remetente — é `privado`
  automaticamente quando o remetente é o gestor do destinatário (pode conter conteúdo
  corretivo) e `publico` nos demais casos (deve ser só reconhecimento positivo, sujeito a
  moderação).

### PesquisaClima / PerguntaClima / RespostaClima / RespostaClimaParticipacao

Pesquisa de clima organizacional desenhada para anonimato real.

- **Regras estruturais:** `RespostaClima` não tem nenhuma coluna de identidade (só a pergunta,
  o departamento e a nota); `RespostaClimaParticipacao` existe só para impedir voto duplicado e
  nunca é cruzada com as respostas; resultados agregados abaixo do mínimo de respostas
  configurado são suprimidos.

## 8. Comunicação, solicitações e conteúdo

### SolicitacaoRH

Pedido do colaborador ao RH (alteração cadastral, declaração, documento avulso, outra
demanda).

- **Regras estruturais:** decisão (atender/indeferir) não altera o cadastro automaticamente —
  o RH aplica a mudança pelo fluxo normal, se aprovada.

### Comunicado / ArtigoFaq / Feriado

Conteúdo publicado por RH/Admin: comunicados internos (com público-alvo: todos, departamento
ou perfil), base de conhecimento (FAQ) e calendário de feriados.

### Onboarding / OnboardingItem

Checklist de integração de um colaborador recém-admitido, com 13 itens fixos por categoria,
cada um com responsável definido (RH, colaborador ou gestor).

### DelegacaoAprovacao

Delegação temporária de um titular (User) para um substituto, por escopo (férias, ausência,
documento, desligamento, correção de ponto, solicitação RH, ou todas).

- **Regras estruturais:** bloqueia autodelegação; hoje é CRUD isolado — nenhum fluxo de
  aprovação consulta a delegação para trocar o aprovador automaticamente (trabalho futuro).

## 9. Auditoria

### Auditoria

Registro append-only de ações relevantes sobre as entidades acima: quem (`user_id`), o quê
(`acao`, `recurso`, `registro_id`), quando (`created_at`), valor anterior/novo e justificativa,
quando aplicável.

- **Regras estruturais:** nem toda ação de escrita é auditada hoje — `docs/regras-de-negocio.md`
  (seção 13.3) lista as lacunas conhecidas.
