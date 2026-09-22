## Why

O ConectaRH acumulou, ao longo de multiplas sessoes de desenvolvimento, dezenas de endpoints com regras de validacao, autorizacao e transicao de estado implementadas diretamente no codigo XanoScript (`xano-workspace/`). Nenhum documento unico consolida essas regras hoje — elas so sao descobriveis lendo cada arquivo de tabela e endpoint individualmente. Isso dificulta onboarding no projeto, revisao de conformidade e a continuidade segura do desenvolvimento, alem de ser um dos entregaveis esperados do projeto integrador (documentacao de decisoes).

## What Changes

- Produzir um documento de referencia unico que mapeia, por dominio funcional do ConectaRH, as regras de negocio ja implementadas no codigo: regras de validacao de entrada, regras de autorizacao (quem pode executar cada acao e sob qual escopo), maquinas de estado (transicoes validas por entidade) e o que e registrado em auditoria.
- Nao altera nenhum comportamento do sistema. E um levantamento do que ja existe no codigo publicado, nao uma proposta de mudanca funcional — por isso esta mudanca declara `skip_specs: true` e nao produz uma spec delta.
- A fonte de verdade para o mapeamento e o codigo em `xano-workspace/` (tabelas, functions, endpoints de API) e os artefatos OpenSpec ja existentes do change `conectarh.gestao`.

## Capabilities

Nenhuma. Mudanca de documentacao pura, sem alteracao de comportamento do sistema (`skip_specs: true` em `.openspec.yaml`).

## Impact

- Novo arquivo de documentacao no repositorio, referenciavel por qualquer pessoa que precise entender as regras de negocio do sistema sem ler o codigo inteiro.
- Nenhum impacto em codigo de producao, API, dados ou dependencias — nenhum arquivo em `xano-workspace/` e alterado por esta mudanca.
