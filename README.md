# ConectaRH

Plataforma integrada de RH que centraliza rotinas hoje dispersas em uma empresa: identidade e
autorização por perfil (Admin, RH, Gestor, Colaborador), estrutura organizacional, jornada e
ponto, documentos, férias, ausências, desligamento e desenvolvimento de colaboradores
(avaliações, metas, PDI, pesquisa de clima).

## Sobre o projeto

RH, gestores e colaboradores hoje dependem de processos e ferramentas dispersas (planilhas,
e-mail, controles paralelos) para tarefas como controle de jornada, cadastro e histórico
profissional, gestão de documentos, solicitação de férias/ausências, avaliação de desempenho e
desligamento. O ConectaRH resolve isso centralizando essas rotinas em uma única plataforma, com
autorização consistente por perfil e escopo, e com toda decisão relevante auditável (quem, o
quê, quando e por quê).

Um dos pilares do projeto é o motor de resolução de regras de negócio: parâmetros de jornada,
banco de horas e férias são resolvidos por uma matriz de contrato que pode ser sobrescrita por
norma legal, instrumento coletivo (acordo/convenção) ou exceção individual, sempre com histórico
auditável de qual regra foi aplicada e por quê — cobrindo cenários reais de conformidade
trabalhista brasileira (eSocial, CTPS Digital, Sistema Mediador/MTE).

Visão completa do projeto (problema, objetivos, escopo, restrições) em
[`docs/project-overview.md`](docs/project-overview.md); conceitos do domínio e relacionamentos
em [`docs/domain-model.md`](docs/domain-model.md).

### Principais funcionalidades

- Login com token de curta duração + validação obrigatória por código de acesso (OTP) por
  e-mail, com bloqueio após tentativas inválidas.
- Cadastro e histórico profissional de colaboradores, cargos e departamentos.
- Ponto com correção sujeita a aprovação, e banco de horas.
- Documentos com fluxo de aprovação, vencimento automático e retenção.
- Férias e ausências, com verificação de conflito.
- Fluxo completo de desligamento (imediato ou aviso prévio).
- Avaliação de desempenho, metas, PDI, reconhecimento e pesquisa de clima anônima.
- Instrumentos normativos e regras de override por contrato, com aprovação e versionamento.
- Central de solicitações, comunicados, FAQ, calendário, onboarding, organograma e auditoria.

## Stack

- **Backend:** [Xano](https://xano.com) + Script Xano (XanoScript), versionado em `xano-workspace/`
- **Frontend:** [Streamlit](https://streamlit.io) — ainda não iniciado
- **E-mail transacional:** [Brevo](https://www.brevo.com)
- **Design:** Figma (design system, protótipos e handoff — assets exportados não são versionados
  neste repositório)
- **Planejamento e especificação:** [OpenSpec](https://github.com/Fission-AI/OpenSpec), em `openspec/`

## Estrutura do repositório

```
AGENTS.md           Instrucoes para agentes de IA que trabalham no projeto
docs/
  project-overview.md   O que e o projeto (visao, objetivos, escopo)
  domain-model.md        Conceitos do dominio e relacionamentos
  regras-de-negocio.md   Regras de negocio ja implementadas, mapeadas do codigo
openspec/
  config.yaml       Contexto e regras injetados pelo OpenSpec em cada workflow
  specs/            Comportamento consolidado do sistema (preenchido ao arquivar changes)
  changes/          Propostas, specs, design e tasks das mudancas em planejamento
    archive/        Historico de mudancas concluidas e arquivadas
xano-workspace/     Backend Xano em XanoScript (tabelas, funcoes e endpoints de API)
  table/            Definicoes de tabelas do banco relacional
  function/         Funcoes reutilizaveis (ex.: validacao de CPF, resolucao de regras)
  api/              Grupos de endpoints de API, organizados por dominio
  task/             Rotinas agendadas (aguardando upgrade de plano Xano para publicar)
```

O plano funcional em andamento está em `openspec/changes/conectarh.gestao/` (proposta, design,
especificações e lista de tarefas). `docs/regras-de-negocio.md` documenta as regras de negócio
já implementadas, mapeadas diretamente do código do backend.

> A proposta de gestão de vagas e candidaturas (ConectaRH Vagas) foi retirada deste repositório
> e não está em planejamento ativo no momento.

## Setup

1. Clone o repositório.
2. Backend: importe o conteúdo de `xano-workspace/` no workspace Xano do projeto (via
   sincronização Git do Xano, ou pela CLI `xano workspace push`) para aplicar tabelas, funções e
   endpoints.
3. Configure a variável de ambiente `BREVO_API_KEY` no workspace Xano (chave de API, não a chave
   SMTP) para o envio de e-mails transacionais (código de acesso, notificações).
4. Frontend: a estrutura Streamlit ainda será adicionada (ver
   `openspec/changes/conectarh.gestao/tasks.md`).
5. Consulte `openspec/changes/conectarh.gestao/design.md` para decisões de arquitetura e
   `specs/` para o comportamento esperado de cada funcionalidade.

## Estratégia de branches

- `master`: sempre reflete o estado estável e implantável.
- `feature/<área>-<descrição-curta>`: uma branch por tarefa ou grupo de tarefas relacionadas
  do `tasks.md` (ex.: `feature/auth-login-token`, `feature/desligamento-fluxo`).
- Todo trabalho é integrado a `master` por Pull Request, com pelo menos uma revisão do grupo antes
  do merge.
- Commits referenciam a tarefa do `tasks.md` que estão implementando quando aplicável.

## Responsabilidades do grupo

| Integrante | Área |
| --- | --- |
| Leonardo dos Santos | Backend (Xano / XanoScript) |
| Nicolas Risato | Frontend (Streamlit) |
| Matheus | Apoio no Backend e documentação do projeto |
