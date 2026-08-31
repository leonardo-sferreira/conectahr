## Context

O change `conectarh.gestao` (em andamento, nao arquivado) ja implementou uma parte substancial do backend do ConectaRH em `xano-workspace/`: dezenas de tabelas e mais de cem endpoints de API, cada um com suas proprias regras de validacao, autorizacao e transicao de estado escritas diretamente no codigo XanoScript. A `specs/conectahr/spec.md` desse change descreve o comportamento em nivel de requisito (SHALL + cenarios), mas nao desce ao nivel de detalhe operacional que normalmente vive so no codigo: valores exatos de enum aceitos, quem exatamente pode chamar cada endpoint, e a maquina de estados completa de cada entidade.

Ver proposal.md - Why para a motivacao completa.

## Goals / Non-Goals

**Goals:**

- Definir a estrutura e o escopo do documento de regras de negocio antes de escreve-lo, para que o levantamento seja completo e organizado por dominio, nao uma lista solta.
- Garantir que o documento seja derivado do codigo real (`xano-workspace/`), nao da memoria ou de suposicoes — cada regra documentada deve ser rastreavel a um arquivo especifico.

**Non-Goals:**

- Nao e objetivo desta mudanca alterar, corrigir ou completar nenhuma regra de negocio existente — inconsistencias encontradas durante o levantamento sao anotadas no documento, nao corrigidas no codigo aqui.
- Nao cobre os dominios cujo backend ainda nao foi implementado (ex.: motor de resolucao de regras contratuais 4.11-4.13/4.17, quarentena de arquivos real, outbox de e-mail) — o documento mapeia o que existe, nao o que esta planejado.

## Decisions

### Escopo e fonte de verdade

O documento cobre exclusivamente os dominios com backend ja implementado em `xano-workspace/`: identidade e autenticacao, sessoes, colaboradores e vinculo profissional, cargos/departamentos, ponto e correcao, ferias, ausencias, desligamento, documentos (incluindo holerite/IR e pendencias), banco de horas, delegacao de aprovacao, instrumentos normativos e regras de override, avaliacao e desenvolvimento (ciclos, metas, PDI, reconhecimento, clima, carreira, contestacao), central de solicitacoes, comunicados, FAQ, calendario, catalogos, parametros protegidos e auditoria. Cada regra documentada referencia o arquivo de origem (`xano-workspace/table/*.xs` ou `xano-workspace/api/**/*.xs`), permitindo conferencia direta contra o codigo.

Alternativa considerada: derivar o documento so da `specs/conectahr/spec.md` existente, rejeitada porque a spec descreve comportamento em nivel de requisito e nao contem o detalhe operacional (valores de enum, perfis exatos autorizados, nomes de campo) que e o proposito deste levantamento.

### Estrutura do documento

Um unico arquivo Markdown (`docs/regras-de-negocio.md`), organizado por dominio funcional (uma secao por dominio, na mesma ordem dos `api_group` do workspace). Cada dominio traz, quando aplicavel: as entidades e seus campos-chave, as regras de validacao de entrada, uma tabela de autorizacao (perfil x acao), a maquina de estados (transicoes validas), e o que e auditado. Inconsistencias ou decisoes de plataforma relevantes encontradas durante o levantamento (ex.: limitacoes do Xano ja registradas na memoria do projeto) sao citadas onde relevante, sem duplicar o conteudo completo dessas notas.

Alternativa considerada: um arquivo por dominio (varios arquivos pequenos), rejeitada por fragmentar a leitura de algo que se beneficia de ser consultado como referencia unica e pesquisavel.

## Risks / Trade-offs

- [O levantamento fica desatualizado assim que o codigo mudar] -> Aceito conscientemente: este e um retrato do estado atual, nao um documento vivo sincronizado automaticamente. Fica registrado no topo do documento a data do levantamento e a recomendacao de revisa-lo apos mudancas relevantes no backend.
- [Domínio extenso demais para cobrir com precisao total numa unica passada] -> Priorizar exatidao sobre completude: e preferivel que cada regra documentada esteja correta e rastreavel do que tentar cobrir 100% dos ~150 endpoints com risco de erro. Gaps conhecidos ficam explicitamente marcados como "nao coberto" em vez de omitidos silenciosamente.
