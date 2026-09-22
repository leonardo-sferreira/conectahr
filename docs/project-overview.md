# Project Overview — ConectaRH

## 1. Visão geral

ConectaRH é uma plataforma integrada de RH que centraliza rotinas hoje dispersas em uma
empresa: identidade e autorização por perfil, estrutura organizacional, jornada e ponto,
documentos, férias, ausências, desligamento e desenvolvimento de colaboradores (avaliações,
metas, PDI, pesquisa de clima). Um dos pilares do projeto é o motor de resolução de regras de
negócio: parâmetros de jornada, banco de horas e férias podem ser sobrescritos por norma
legal, instrumento coletivo (acordo/convenção) ou exceção individual, sempre com histórico
auditável de qual regra foi aplicada e por quê.

## 2. Problema

RH, gestores e colaboradores hoje dependem de processos e ferramentas dispersas (planilhas,
e-mail, controles paralelos) para tarefas como controle de jornada, cadastro e histórico
profissional, gestão de documentos, solicitação de férias/ausências, avaliação de desempenho e
desligamento. Isso dificulta rastreabilidade, auditoria e conformidade com a legislação
trabalhista brasileira (eSocial, CTPS Digital, Sistema Mediador/MTE), além de exigir retrabalho
manual para consolidar indicadores de RH.

## 3. Objetivos

- Entregar um MVP demonstrável, documentado e implantável que cubra o ciclo de vida do
  colaborador: admissão, jornada, documentos, férias/ausências, desenvolvimento e
  desligamento.
- Centralizar autorização por perfil (Admin, RH, Gestor, Colaborador) e escopo organizacional
  (departamento, propriedade do registro), aplicada de forma consistente no backend.
- Tornar auditável toda decisão relevante (aprovações, rejeições, alterações de cadastro,
  aplicação de regra), com responsável e justificativa registrados.
- Resolver parâmetros de jornada/banco de horas/férias por uma matriz de contrato que pode ser
  sobrescrita por norma legal, instrumento coletivo ou exceção individual — sem decidir
  automaticamente conflitos jurídicos.

## 4. Público-alvo / usuários

- **Admin**: acesso administrativo amplo, equivalente a RH nas ações mapeadas até aqui.
- **RH**: cria e gerencia colaboradores, cargos, departamentos, documentos, instrumentos
  normativos e regras de override; decide férias, ausências, desligamentos e solicitações.
- **Gestor**: gerencia o próprio departamento — aprova correções de ponto e desligamentos da
  equipe, acompanha metas e avaliações, envia reconhecimento (público ou privado).
- **Colaborador**: registra o próprio ponto, solicita férias/ausências/correções, envia
  documentos, participa de avaliações, metas, PDI e pesquisa de clima.
- **Candidato**: perfil de um projeto futuro de recrutamento (ConectaRH Vagas), fora do escopo
  atual deste repositório — ver seção 5.

## 5. Escopo

**No MVP (`conectarh.gestao`):** identidade/autenticação (login + OTP por e-mail), autorização
por perfil e escopo, cadastro de colaboradores/cargos/departamentos com histórico profissional,
dados bancários do colaborador, ponto e correção de ponto, banco de horas, documentos (incl.
holerite/informe de rendimentos) com vencimento e retenção, férias e ausências, desligamento
(imediato ou aviso prévio), avaliação de desempenho com contestação, metas, PDI,
reconhecimento, pesquisa de clima anônima, instrumentos normativos e regras de override,
central de solicitações do colaborador ao RH, comunicados internos, FAQ, calendário
organizacional, onboarding, organograma, busca global, notificações internas, auditoria,
indicadores e exportações.

**Fora deste repositório:** gestão de vagas e candidaturas (ConectaRH Vagas) foi cogitada como
extensão do ConectaRH, mas a proposta correspondente foi retirada deste repositório e não está
em planejamento ativo no momento.

**Fora de escopo:** cálculo ou emissão de folha de pagamento (holerite é apenas anexado pelo
RH, gerado fora do ConectaRH); conformidade completa de ponto eletrônico como REP-P/REP-A/REP-C
(o registro de ponto do MVP é tratado como controle interno experimental); decisão automática
de conflitos jurídicos na resolução de regras contratuais; promoção automática por plano de
carreira.

## 6. Principais funcionalidades

- Login com token de curta duração + validação obrigatória por código de acesso (OTP) enviado
  por e-mail, com bloqueio após tentativas inválidas e troca de senha obrigatória no primeiro
  acesso.
- Cadastro e histórico profissional de colaboradores, cargos e departamentos, com vínculo
  gestor-departamento.
- Registro de ponto com marcação em ordem (entrada → intervalo → saída), solicitação de
  correção com aprovação/recusa, e banco de horas em lançamentos append-only.
- Envio e aprovação de documentos (com estados `pendente_analise` → `aprovado`/`rejeitado` →
  `vencido`/`substituido` → `arquivado`), pendências de documento e vencimento automático.
- Solicitação e decisão de férias e ausências, com verificação informativa de conflito
  (antecedência, período aquisitivo, sobreposição, colegas de departamento).
- Fluxo completo de desligamento (imediato ou aviso prévio), com aprovação exclusiva do RH e
  desativação de acesso.
- Ciclos de avaliação, competências, avaliação privada (gestor-colaborador), contestação,
  metas com check-in, PDI, reconhecimento público/privado com moderação, e pesquisa de clima
  desenhada para anonimato real (sem coluna de identidade na resposta).
- Instrumentos normativos (acordo/convenção coletiva, norma legal etc.) e regras de override
  por contrato, com aprovação, versionamento e bloqueio de autoaprovação.
- Central de solicitações do colaborador ao RH, comunicados internos, FAQ, calendário com
  feriados e ausências aprovadas, onboarding com checklist, organograma e busca global.
- Auditoria de decisões relevantes (`quem`, `o quê`, `quando`, `justificativa`).

## 7. Requisitos e restrições importantes

- Toda regra de autorização é verificada no backend a cada requisição (perfil normalizado,
  usuário ainda ativo) — nunca confiar em estado do frontend.
- CPF é validado localmente pelo algoritmo dos dígitos verificadores, sem API externa.
- Dados bancários do colaborador são visíveis para o próprio colaborador e para o RH, nunca
  para o Gestor.
- Exclusão física é bloqueada para entidades com trilha de auditoria (documentos, ausências) —
  o padrão é arquivamento, não exclusão.
- API versionada sob `/api/v1/`, com identificador de rastreamento por requisição.
- Conformidade com a LGPD na proteção de dados pessoais e sensíveis.

## 8. Arquitetura tecnológica

- **Backend:** [Xano](https://xano.com) + XanoScript, versionado em `xano-workspace/`
  (`table/`, `function/`, `api/`, `task/`).
- **Frontend:** [Streamlit](https://streamlit.io) — ainda não iniciado.
- **E-mail transacional:** [Brevo](https://www.brevo.com).
- **Design:** Figma (design system, protótipos e handoff — assets exportados não são
  versionados no repositório).
- **Planejamento e especificação:** [OpenSpec](https://github.com/Fission-AI/OpenSpec), em
  `openspec/`, schema `spec-driven`.

## 9. Princípios de desenvolvimento

- Desenvolvimento incremental via OpenSpec: Explore → Propose → Review → Apply → Archive.
- Reutilizar padrões de código e de domínio já estabelecidos em vez de criar um padrão novo
  para o mesmo problema.
- Mudanças puramente documentais (levantamento de regras já implementadas, por exemplo) não
  alteram comportamento e declaram `skip_specs: true`.

## 10. Segurança e integridade

- Autorização por perfil (Admin/RH/Gestor/Colaborador) e por escopo (departamento, propriedade
  do registro), sempre aplicada no backend.
- Ações sensíveis (aprovações, rejeições, alterações de cadastro, aplicação de regra de
  override) são auditadas com responsável, justificativa e, quando aplicável, valor
  anterior/novo.
- Anonimato real na pesquisa de clima: a resposta não carrega identidade do respondente, e a
  tabela de controle de participação nunca é cruzada com as respostas.
- Proteção de dados pessoais e sensíveis conforme a LGPD (minimização, finalidade, acesso por
  necessidade, retenção controlada).

## 11. Estratégia de desenvolvimento

- Branch `master` sempre reflete o estado estável e implantável; trabalho ocorre em branches
  `feature/<área>-<descrição-curta>` integradas por Pull Request com revisão do grupo.
- Commits referenciam a tarefa de `tasks.md` que estão implementando, quando aplicável.
- Mudanças relevantes são especificadas (proposal/specs/design/tasks) antes da implementação;
  o grupo revisa cada artefato antes de autorizar o `Apply`.

## 12. Fonte de verdade e documentação

- `docs/regras-de-negocio.md` documenta as regras de negócio já implementadas, mapeadas
  diretamente do código do backend (`xano-workspace/`) — é um retrato do código em uma data,
  não sincronizado automaticamente.
- `openspec/changes/conectarh.gestao/` contém a proposta, o design e as tarefas do MVP em
  andamento.
- `openspec/specs/` passa a refletir o comportamento consolidado do sistema à medida que
  changes são arquivadas.
