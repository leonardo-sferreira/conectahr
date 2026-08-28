# ConectaRH

Plataforma integrada de RH para identidade, autorização, estrutura organizacional, jornada,
documentos, férias, ausências, desligamento e desenvolvimento de colaboradores.

## Stack

- **Backend:** [Xano](https://xano.com) + Script Xano (XanoScript), versionado em `xano-workspace/`
- **Frontend:** [Reflex](https://reflex.dev)
- **E-mail transacional:** SendGrid
- **Design:** Figma (design system, protótipos e handoff)
- **Planejamento e especificação:** [OpenSpec](https://github.com/Fission-AI/OpenSpec), em `openspec/`

## Estrutura do repositório

```
openspec/          Propostas, specs, design e tasks das mudanças planejadas
xano-workspace/     Backend Xano em XanoScript (tabelas, funções e endpoints de API)
  table/            Definições de tabelas do banco relacional
  function/         Funções reutilizáveis (ex.: validação de CPF)
  api/              Grupos de endpoints de API, organizados por domínio
```

O plano funcional completo do MVP está em
`openspec/changes/criar-sistema-conectahr/` (proposta, design, especificações e lista de tarefas).

## Setup

1. Clone o repositório.
2. Backend: importe o conteúdo de `xano-workspace/` no workspace Xano do projeto (via
   sincronização Git do Xano) para aplicar tabelas, funções e endpoints.
3. Frontend: a estrutura Reflex ainda será adicionada (ver
   `openspec/changes/criar-sistema-conectahr/tasks.md`, tarefa 1.2).
4. Consulte `openspec/changes/criar-sistema-conectahr/design.md` para decisões de arquitetura
   e `specs/conectahr/spec.md` para o comportamento esperado de cada funcionalidade.

## Estratégia de branches

- `main`: sempre reflete o estado estável e implantável.
- `feature/<área>-<descrição-curta>`: uma branch por tarefa ou grupo de tarefas relacionadas
  do `tasks.md` (ex.: `feature/auth-login-token`, `feature/desligamento-fluxo`).
- Todo trabalho é integrado a `main` por Pull Request, com pelo menos uma revisão do grupo antes
  do merge.
- Commits referenciam a tarefa do `tasks.md` que estão implementando quando aplicável.

## Responsabilidades do grupo

_A preencher pelo grupo: nome de cada integrante e a área do MVP (identidade/autorização,
cadastro organizacional, jornada/ausências, documentos, avaliação/desenvolvimento,
integração/entrega) pela qual é responsável._

| Integrante | Área |
| --- | --- |
| | |
