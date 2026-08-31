# ConectaRH

Plataforma integrada de RH para centralizar rotinas hoje dispersas em uma empresa: identidade e
autorização por perfil (Admin, RH, Gestor, Colaborador), estrutura organizacional, jornada e
ponto, documentos, férias, ausências, desligamento e desenvolvimento de colaboradores (avaliações,
metas, PDI, pesquisa de clima).

Um dos pilares do projeto é o motor de resolução de regras de negócio: parâmetros de jornada,
banco de horas e férias são resolvidos por uma matriz de contrato que pode ser sobrescrita por
norma legal, instrumento coletivo (acordo/convenção) ou exceção individual, sempre com histórico
auditável de qual regra foi aplicada e por quê — cobrindo cenários reais de conformidade
trabalhista brasileira (eSocial, CTPS Digital, Sistema Mediador/MTE).

## Stack

- **Backend:** [Xano](https://xano.com) + Script Xano (XanoScript), versionado em `xano-workspace/`
- **Frontend:** [Reflex](https://reflex.dev) — ainda não iniciado
- **E-mail transacional:** [Brevo](https://www.brevo.com)
- **Design:** Figma (design system, protótipos e handoff — assets exportados não são versionados
  neste repositório)
- **Planejamento e especificação:** [OpenSpec](https://github.com/Fission-AI/OpenSpec), em `openspec/`

## Estrutura do repositório

```
openspec/          Propostas, specs, design e tasks das mudancas planejadas
docs/               Documentacao gerada a partir do codigo (ex.: regras-de-negocio.md)
xano-workspace/     Backend Xano em XanoScript (tabelas, funcoes e endpoints de API)
  table/            Definicoes de tabelas do banco relacional
  function/         Funcoes reutilizaveis (ex.: validacao de CPF, resolucao de regras)
  api/              Grupos de endpoints de API, organizados por dominio
  task/             Rotinas agendadas (aguardando upgrade de plano Xano para publicar)
```

O plano funcional em andamento está em `openspec/changes/conectarh.gestao/` (proposta, design,
especificações e lista de tarefas). `docs/regras-de-negocio.md` documenta as regras de negócio já
implementadas, mapeadas diretamente do código do backend.

## Setup

1. Clone o repositório.
2. Backend: importe o conteúdo de `xano-workspace/` no workspace Xano do projeto (via
   sincronização Git do Xano, ou pela CLI `xano workspace push`) para aplicar tabelas, funções e
   endpoints.
3. Configure a variável de ambiente `BREVO_API_KEY` no workspace Xano (chave de API, não a chave
   SMTP) para o envio de e-mails transacionais (código de acesso, notificações).
4. Frontend: a estrutura Reflex ainda será adicionada (ver
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

_A preencher pelo grupo: nome de cada integrante e a área do MVP (identidade/autorização,
cadastro organizacional, jornada/ausências, documentos, avaliação/desenvolvimento,
integração/entrega) pela qual é responsável._

| Integrante | Área |
| --- | --- |
| | |
| | |
| | |
