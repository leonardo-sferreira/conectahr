# AGENTS.md — ConectaRH

Instruções para agentes de IA que trabalham neste repositório. Este arquivo define **como**
trabalhar no projeto. Para entender **o que é** o projeto, leia primeiro:

- [`docs/project-overview.md`](docs/project-overview.md) — visão geral, objetivo, escopo.
- [`docs/domain-model.md`](docs/domain-model.md) — conceitos do domínio e relacionamentos.
- [`docs/regras-de-negocio.md`](docs/regras-de-negocio.md) — regras já implementadas, mapeadas do código.
- [`openspec/config.yaml`](openspec/config.yaml) — contexto e regras que o OpenSpec injeta em cada workflow.

## Documentação

- Antes de propor ou implementar uma mudança relevante, consultar os documentos de contexto
  acima e, quando aplicável, o `design.md` do change `conectarh.gestao` (decisões
  arquiteturais já tomadas para o MVP).
- Regras de negócio novas ou alteradas por uma change devem ser refletidas em
  `docs/regras-de-negocio.md` depois da implementação (ou marcadas para revisão), para o
  documento não ficar desatualizado em relação ao código.

## Arquitetura

- Respeitar a stack definida: backend em Xano/XanoScript (`xano-workspace/`), frontend em
  Streamlit, e-mail transacional via Brevo. Não introduzir tecnologia alternativa sem
  justificativa explícita no `design.md` da change.
- O backend é responsável por regras de negócio, autorização e persistência. O frontend nunca
  deve ser tratado como mecanismo de segurança.
- Seguir os padrões arquiteturais já estabelecidos no código existente (ex.: verificação de
  identidade/perfil recarregando o usuário a cada endpoint, escopo por departamento via
  `gestor_colaborador_id`, padrão append-only para banco de horas e check-ins) em vez de
  introduzir um padrão novo para o mesmo problema.

## Código

- Reutilizar tabelas, funções e padrões de endpoint já existentes em `xano-workspace/` quando
  apropriado. Evitar duplicar lógica de autorização ou de validação já resolvida em outro
  endpoint do mesmo domínio.
- Não modificar funcionalidades fora do escopo da change atual sem justificativa registrada na
  proposta ou no design.

## Segurança

- Regras de autorização (perfil × escopo) são sempre aplicadas no backend, nunca só no
  frontend.
- Dados sensíveis (senha, código de acesso/OTP, dados bancários, documentos, feedback privado)
  seguem o mesmo padrão de proteção já usado no código: campos privados, acesso restrito por
  dono do registro ou por perfil administrativo (RH/Admin), nunca por Gestor quando o domínio
  já exclui esse acesso.
- Dados pessoais e sensíveis devem observar a LGPD: minimização, finalidade declarada, acesso
  por necessidade e retenção controlada.

## Desenvolvimento

- O projeto é desenvolvido incrementalmente com OpenSpec (`openspec/`), seguindo o ciclo
  Explore → Propose → Review → Apply → Archive.
- Mudanças funcionais relevantes devem ser especificadas (proposal/specs/design/tasks) antes
  da implementação. Mudanças puramente documentais podem declarar `skip_specs: true`.
- Commits referenciam a tarefa de `tasks.md` que estão implementando, quando aplicável (ex.:
  `7.8`, `1.11`). Trabalho é integrado a `master` por Pull Request.

## Testes

- Toda mudança funcional deve ter uma estratégia de verificação descrita em `tasks.md` (o que
  testar e como confirmar que o comportamento esperado foi atingido), já que o Xano não expõe
  um test runner tradicional para o backend.
- Antes de concluir uma tarefa, verificar o comportamento no próprio workspace Xano (ou nos
  testes documentados em `docs/testes-integracao.md` / `docs/testes-seguranca.md`) em vez de
  assumir que a implementação está correta apenas pela leitura do código.
