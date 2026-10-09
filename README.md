# ConectaRH

Plataforma integrada de RH que centraliza rotinas hoje dispersas em uma empresa: identidade e
autorização por perfil (Admin, RH, Gestor, Colaborador), estrutura organizacional, jornada e ponto,
documentos, férias, ausências, desligamento e desenvolvimento de colaboradores (avaliações, metas, PDI,
pesquisa de clima). É um **trabalho acadêmico** desenvolvido em grupo.

**Versão atual: [v0.2.0](https://github.com/leonardo-sferreira/conectahr/releases)**: backend, segurança,
LGPD, especificações e documentação concluídos; o frontend Streamlit está parcial (tela de entrada e início).

## Sobre o projeto

RH, gestores e colaboradores hoje dependem de processos e ferramentas dispersas (planilhas, e-mail,
controles paralelos) para tarefas como controle de jornada, cadastro e histórico profissional, gestão de
documentos, solicitação de férias e ausências, avaliação de desempenho e desligamento. O ConectaRH
centraliza essas rotinas em uma única plataforma, com autorização consistente por perfil e escopo, e com
toda decisão relevante auditável (quem, o quê, quando e por quê).

Um dos pilares é o motor de resolução de regras de negócio: parâmetros de jornada, banco de horas e férias
são resolvidos por uma matriz de contrato que pode ser sobrescrita por norma legal, instrumento coletivo
(acordo ou convenção) ou exceção individual, sempre com histórico auditável de qual regra foi aplicada e
por quê.

Visão completa em [`docs/project-overview.md`](docs/project-overview.md); arquitetura em
[`docs/arquitetura.md`](docs/arquitetura.md); conceitos do domínio em
[`docs/domain-model.md`](docs/domain-model.md).

## Status do projeto

| Área | Situação |
|---|---|
| **Backend (Xano)** | Concluído: 50 tabelas, 14 funções e 189 endpoints em 10 grupos de API (184 autenticados) |
| **Segurança** | Concluída: guarda de acesso em todo endpoint autenticado, sessão ligada ao token, revogação em massa, bloqueio de autoaprovação, hash dos códigos de acesso, swagger desligado |
| **LGPD** | Documentação e controles concluídos (registro de operações, aviso, RIPD, retenção, direitos do titular, anonimização, menores de 18 anos). Prazos e bases legais são sugestões acadêmicas |
| **Especificações (OpenSpec)** | Spec principal com 65 requisitos e 201 cenários; 6 changes arquivadas |
| **Documentação e evidências** | Concluídas, com testes por HTTP por perfil em [`docs/evidencias/`](docs/evidencias/) |
| **Frontend (Streamlit)** | Parcial: tela de entrada (login em dois passos, troca de senha, redefinição) e início. As demais telas dependem do protótipo do Figma |

O que falta está na change [`concluir-frontend-streamlit`](openspec/changes/concluir-frontend-streamlit/):
57 tarefas (telas do Figma, acessibilidade, deploy, fontes locais e a tela "Privacidade").

### Principais funcionalidades

- Login com senha e **código de acesso por e-mail** (guardado como hash), token de 1 hora ligado a uma
  sessão, bloqueio após tentativas inválidas e alerta de acesso suspeito.
- Cadastro e histórico profissional de colaboradores, cargos e departamentos; onboarding e organograma.
- Ponto com correção sujeita a aprovação e banco de horas (controle interno experimental, ver abaixo).
- Documentos por link de domínio aprovado, com aprovação, vencimento e prazo de retenção.
- Férias e ausências com verificação de conflito; o Gestor decide a própria equipe e há delegação por
  vigência.
- Desligamento imediato ou com aviso prévio.
- Avaliação de desempenho, metas, PDI, reconhecimento e pesquisa de clima anônima.
- Instrumentos normativos e regras de override por contrato, com aprovação e versionamento.
- Central de solicitações, comunicados, FAQ, calendário, painel do Gestor, indicadores e auditoria.
- **Rotina diária manual** (RH/Admin) para as transições que dependem de data, com o pendente visível em
  `status_operacional`.
- **Privacidade:** exportação dos dados do titular, pedido LGPD com prazo, preferências de privacidade e
  anonimização de colaborador desligado.

## Stack

- **Backend:** [Xano](https://xano.com) + XanoScript, versionado em `xano-workspace/` (plano gratuito)
- **Frontend:** [Streamlit](https://streamlit.io), em `frontend/`
- **E-mail transacional:** [Brevo](https://www.brevo.com)
- **Design:** Figma (design system, protótipos e handoff; assets exportados não são versionados)
- **Planejamento e especificação:** [OpenSpec](https://github.com/Fission-AI/OpenSpec), em `openspec/`
- **Validação:** GitHub Actions (`.github/workflows/validar.yml`)

## Estrutura do repositório

```
AGENTS.md           Instruções para agentes de IA (fonte única; CLAUDE.md e GEMINI.md apontam para ele)
docs/
  project-overview.md    O que é o projeto (visão, objetivos, escopo)
  arquitetura.md         Arquitetura e padrões
  domain-model.md        Conceitos do domínio e relacionamentos
  regras-de-negocio.md   Regras de negócio implementadas, mapeadas do código
  demonstracao.md        Roteiro para reproduzir o fluxo principal
  deploy.md              Ambientes, configuração, flags e plano de rollback
  monitoramento.md       Sessões, monitoramento operacional, backup e recuperação
  backlog-rep.md         Ponto eletrônico: o que não é feito e o backlog de conformidade
  lgpd/                  Registro de operações, aviso, RIPD, operadores, retenção, incidentes
  evidencias/            Resultado dos testes, sem dados pessoais
frontend/           App Streamlit (app.py, páginas, theme.py, api_client.py) e AGENTS.md próprio
openspec/
  specs/            Comportamento consolidado do sistema (spec principal)
  changes/          Mudanças em andamento
    archive/        Histórico de mudanças concluídas e arquivadas
tools/              checar_endpoints.py (guarda de acesso) e smoke_frontend.py (tela de entrada)
xano-workspace/     Backend Xano em XanoScript
  table/            Tabelas do banco relacional
  function/         Funções reutilizáveis (CPF, regras, rotina diária, hash dos códigos…)
  api/              Grupos de endpoints (ver a tabela abaixo)
  task/             Rotina agendada de referência (desligada: o plano gratuito não publica tarefas)
.github/workflows/  Pipeline "Validar"
```

### Grupos de API

Os 10 grupos de API refletem a **ordem histórica em que foram criados**, não uma divisão limpa por
domínio: por exemplo, avaliações, clima, comunicados e o mural de reconhecimento vivem no grupo de
Colaboradores, e as rotas aninhadas em `colaboradores/{id}/...` aparecem em Ponto e em Documentos, além de
Colaboradores. A tabela diz onde procurar cada módulo. O versionamento é pelo grupo de API (uma mudança
incompatível cria um grupo novo, sem prefixo `/v1/`).

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

## Como rodar

### Backend (Xano)

1. Clone o repositório e instale a [CLI do Xano](https://docs.xano.com), autenticada em um perfil (aqui,
   `ConectaRH`).
2. Publique `xano-workspace/` no workspace do projeto, sempre com `--dry-run` antes. Os padrões `-i` e
   `-e` vão **entre aspas** e os arquivos de grupo ficam de fora:
   ```
   xano workspace push -p ConectaRH -i "api/conecta_rh_ponto/**/*.xs" -e "api/*/conecta_rh_*.xs" --dry-run
   ```
   Detalhes e armadilhas em [`xano-workspace/AGENTS.md`](xano-workspace/AGENTS.md).
3. Configure as variáveis de ambiente no painel do Xano (nunca no repositório):
   `BREVO_API_KEY` (chave de API da Brevo) e `CODIGO_ACESSO_PEPPER` (segredo aleatório longo do hash dos
   códigos). Opcionais: `ARQUIVOS_DOMINIOS_APROVADOS`, `INDICADORES_MINIMO_PESSOAS` e os prazos de
   retenção. Lista completa em [`docs/deploy.md`](docs/deploy.md).

### Frontend (Streamlit)

```
python -m venv .venv
.venv\Scripts\activate          # Linux/Mac: source .venv/bin/activate
pip install -r frontend/requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml    # Linux/Mac: cp
# edite .streamlit/secrets.toml e informe a URL da API do grupo de autenticação
streamlit run frontend/app.py
```

`.streamlit/secrets.toml` não é versionado. Mais detalhes em [`frontend/AGENTS.md`](frontend/AGENTS.md).

### Demonstração

O código de acesso chega por e-mail, então é preciso uma caixa de e-mail real para entrar. O roteiro está
em [`docs/demonstracao.md`](docs/demonstracao.md).

## Qualidade e verificação

- `python tools/checar_endpoints.py` confere a guarda de acesso em todo endpoint autenticado do Xano
  (184 endpoints, 0 falhas).
- `python tools/smoke_frontend.py` confere que a tela de entrada renderiza.
- O pipeline **Validar** roda a cada Pull Request: sintaxe do Python, guarda dos endpoints, teste de
  fumaça do frontend e busca de segredos no repositório.
- Os testes do backend são feitos por HTTP contra o Xano real, por perfil, e registrados em
  [`docs/evidencias/`](docs/evidencias/) (o teste final cobriu os quatro perfis: 43 de 43 chamadas como
  esperado, em [`smoke-final.md`](docs/evidencias/smoke-final.md)). Casos que não foram possíveis de testar
  estão marcados como "não verificado", com o motivo.

## Especificações e histórico (OpenSpec)

A spec principal está em [`openspec/specs/conectahr/spec.md`](openspec/specs/conectahr/spec.md). O projeto
seguiu o ciclo Explorar → Propor → Revisar → Aplicar → Arquivar. Mudanças arquivadas em
[`openspec/changes/archive/`](openspec/changes/archive/):

| Change | O que fez |
|---|---|
| `mapear-regras-negocio` | Mapeou as regras de negócio do código para `docs/regras-de-negocio.md` |
| `conectarh.gestao` | O MVP de gestão de RH (backend) |
| `implementar-frontend-streamlit` | Fundação do frontend: navegação, tema, cliente de API e tela de entrada |
| `corrigir-brechas-e-alinhar-documentacao` | Auditoria de segurança e alinhamento da documentação |
| `adequacao-lgpd` | Adequação à LGPD |
| `concluir-mvp-conectarh` | Consolidou e concluiu as quatro anteriores (81 tarefas) |

Em andamento: [`concluir-frontend-streamlit`](openspec/changes/concluir-frontend-streamlit/).

## Limitações conhecidas

- **Plano gratuito do Xano:** 10 requisições a cada 20 segundos, um workspace só, sem tarefas agendadas
  (as rotinas são acionadas por RH/Admin) e **sem upload de arquivo privado** (documento entra por link
  de domínio aprovado; o atestado não é guardado no sistema).
- **Ponto eletrônico:** controle interno experimental, sem certificação (ver abaixo).
- **LGPD:** bases legais e prazos de guarda são sugestões acadêmicas, sem assessoria jurídica. A instância
  do Xano fica nos EUA (inferido pelo IP), o que é uma transferência internacional a tratar.
- **Frontend:** só a tela de entrada e o início; o restante depende do Figma.

## Privacidade e proteção de dados

O ConectaRH trata dados pessoais e sensíveis de colaboradores e segue a LGPD. A documentação está em
[`docs/lgpd/`](docs/lgpd/): [aviso de privacidade](docs/lgpd/aviso-de-privacidade.md),
[registro de operações](docs/lgpd/registro-de-operacoes.md),
[plano de incidentes](docs/lgpd/plano-de-incidentes.md), [RIPD](docs/lgpd/ripd.md),
[operadores](docs/lgpd/operadores.md), [legítimo interesse](docs/lgpd/legitimo-interesse.md) e
[retenção](docs/lgpd/retencao.md). Bases legais e prazos de guarda são sugestões acadêmicas, **a
confirmar com o jurídico** de quem for usar o sistema de verdade.

**Encarregado pelo tratamento de dados pessoais:** a definir (sugestão: o responsável pela documentação).
**Contato:** `privacidade@conectarh.com` (endereço provisório; a caixa precisa ser criada e confirmada). O
mesmo contato consta no aviso de privacidade.

O repositório é **público**: não commite dado pessoal real, senha, token nem chave de serviço.

## Ponto eletrônico: controle interno experimental

O registro de ponto do MVP é um **controle interno experimental**. Ele **não é um REP** e **não possui
certificação nem conformidade** com a Portaria MTP nº 671/2021 (REP-C, REP-A e REP-P). O backlog de
conformidade está em [`docs/backlog-rep.md`](docs/backlog-rep.md).

## Para agentes de IA

O [`AGENTS.md`](AGENTS.md) da raiz é a fonte única de instruções para Codex, Gemini CLI e Claude Code
(`CLAUDE.md` e `GEMINI.md` apontam para ele). `frontend/AGENTS.md` e `xano-workspace/AGENTS.md` trazem só o
que é específico de cada pasta.

## Estratégia de branches e versões

- `master`: sempre reflete o estado estável.
- `feature/CON-XX-descricao`: uma branch por tarefa ou grupo de tarefas, onde `CON-XX` é o card do Jira.
  Enquanto não houver card, a tarefa do `tasks.md` ocupa o lugar (ex.: `feature/lgpd-backend-parte2`).
- Todo trabalho é integrado a `master` por Pull Request, com pelo menos uma revisão do grupo. Nunca há push
  direto no `master`.
- Commits: `CON-XX descrição (tarefa)`; sem card, citam a tarefa do `tasks.md` (ex.: `4.12`).
- **Versões:** as releases do GitHub marcam os marcos do projeto: `v0.1.0` (backend em andamento e
  fundação do OpenSpec) e `v0.2.0` (backend, segurança, LGPD, especificações e documentação concluídos).

## Responsabilidades do grupo

| Integrante | Área |
| --- | --- |
| Leonardo dos Santos | Backend (Xano / XanoScript) |
| Nicolas Risato | Frontend (Streamlit) |
| Matheus | Apoio no Backend e documentação do projeto |
