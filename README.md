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
- **Frontend:** [Streamlit](https://streamlit.io), em `frontend/` (tela de entrada e início; as demais telas dependem do protótipo do Figma)
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
  lgpd/                  Protecao de dados: registro de operacoes, aviso de privacidade, incidentes, RIPD
  evidencias/            Resultado dos testes, sem dados pessoais
openspec/
  config.yaml       Contexto e regras injetados pelo OpenSpec em cada workflow
  specs/            Comportamento consolidado do sistema (preenchido ao arquivar changes)
  changes/          Propostas, specs, design e tasks das mudancas em planejamento
    archive/        Historico de mudancas concluidas e arquivadas
xano-workspace/     Backend Xano em XanoScript (tabelas, funcoes e endpoints de API)
  table/            Definicoes de tabelas do banco relacional
  function/         Funcoes reutilizaveis (ex.: validacao de CPF, resolucao de regras)
  api/              Grupos de endpoints de API (ver a tabela abaixo)
  task/             Rotinas agendadas (aguardando upgrade de plano Xano para publicar)
```

### Grupos de API

Os 10 grupos de API refletem a **ordem histórica em que foram criados**, não uma divisão limpa
por domínio: por exemplo, avaliações, clima, comunicados e o mural de reconhecimento vivem no
grupo de Colaboradores, e as rotas aninhadas em `colaboradores/{id}/...` aparecem em Ponto e em
Documentos, além de Colaboradores. A tabela diz onde procurar cada módulo.

| Grupo (`xano-workspace/api/`) | Módulos |
|---|---|
| `conecta_rh_autenticacao` | login em dois passos (senha + código por e-mail), troca e redefinição de senha, sessões, logout, `status_operacional` |
| `conecta_rh_gestao_de_usuarios` | `usuarios` (criar, editar, ativar e desativar), `delegacoes` e `minhas_delegacoes` |
| `conecta_rh_colaboradores` | colaboradores, vínculo, perfil e dados bancários; onboarding; avaliações, ciclos, metas, PDI e reuniões 1:1; reconhecimentos; pesquisas de clima; comunicados e notificações; solicitações; indicadores; auditoria; instrumentos normativos e regras de override; calendário, feriados, FAQ e `central_de_tarefas` |
| `conecta_rh_departamentos` | departamentos e organograma |
| `conecta_rh_cargos` | cargos |
| `conecta_rh_ponto` | marcação de ponto, correções e banco de horas |
| `conecta_rh_ferias` | solicitações de férias e suas decisões |
| `conecta_rh_ausencias` | ausências e atestados |
| `conecta_rh_documentos` | documentos, documentos obrigatórios, pendências de documento e eventos de SST |
| `conecta_rh_desligamentos` | solicitações de desligamento |

O plano funcional em andamento está em `openspec/changes/concluir-mvp-conectarh/` (proposta,
design e lista de tarefas); as mudanças já concluídas estão em `openspec/changes/archive/`. `docs/regras-de-negocio.md` documenta as regras de negócio
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
4. Frontend: siga "Como rodar" em [`frontend/AGENTS.md`](frontend/AGENTS.md) (ambiente virtual,
   `pip install -r frontend/requirements.txt`, `.streamlit/secrets.toml` a partir do modelo
   `.streamlit/secrets.toml.example` e `streamlit run frontend/app.py`).
5. Consulte `openspec/specs/conectahr/spec.md` para o comportamento esperado e as decisões em
   `openspec/changes/` (plano em andamento) e `openspec/changes/archive/` (histórico).

## Para agentes de IA

O [`AGENTS.md`](AGENTS.md) da raiz é a fonte única de instruções para Codex, Gemini CLI e Claude
Code (`CLAUDE.md` e `GEMINI.md` apontam para ele). `frontend/AGENTS.md` e
`xano-workspace/AGENTS.md` trazem só o que é específico de cada pasta.

## Estratégia de branches

- `master`: sempre reflete o estado estável e implantável.
- `feature/CON-XX-descricao`: uma branch por tarefa ou grupo de tarefas, onde `CON-XX` é o card do
  Jira. Enquanto não houver card, a tarefa do `tasks.md` ocupa o lugar (ex.:
  `feature/lgpd-backend-parte2`).
- Todo trabalho é integrado a `master` por Pull Request, com `CON-XX` no título e pelo menos uma
  revisão do grupo antes do merge. Nunca há push direto no `master`.
- Commits: `CON-XX descrição (tarefa)`; sem card, citam a tarefa do `tasks.md` (ex.: `4.12`).

## Privacidade e proteção de dados

O ConectaRH trata dados pessoais e sensíveis de colaboradores e segue a LGPD. A documentação está em
[`docs/lgpd/`](docs/lgpd/): [aviso de privacidade](docs/lgpd/aviso-de-privacidade.md),
[registro de operações](docs/lgpd/registro-de-operacoes.md),
[plano de incidentes](docs/lgpd/plano-de-incidentes.md), [RIPD](docs/lgpd/ripd.md),
[operadores](docs/lgpd/operadores.md) e [legítimo interesse](docs/lgpd/legitimo-interesse.md).
Bases legais e prazos de guarda são sugestões, **a confirmar com o jurídico**.

**Encarregado pelo tratamento de dados pessoais:** a definir (sugestão: o responsável pela
documentação). **Contato:** `privacidade@conectarh.com` (endereço provisório; a caixa precisa ser
criada e confirmada). O mesmo contato consta no aviso de privacidade.

O repositório é **público**: não commite dado pessoal real, senha, token nem chave de serviço.

## Responsabilidades do grupo

| Integrante | Área |
| --- | --- |
| Leonardo dos Santos | Backend (Xano / XanoScript) |
| Nicolas Risato | Frontend (Streamlit) |
| Matheus | Apoio no Backend e documentação do projeto |
