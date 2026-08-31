## 1. Preparacao

- [x] 1.1 Criar `docs/regras-de-negocio.md` com cabecalho (data do levantamento, fonte de verdade, aviso de que e um retrato do estado atual) e o indice das secoes por dominio definidas em design.md; verificar que o arquivo existe e o indice lista todos os dominios. **Feito:** arquivo criado com cabecalho e indice de 13 secoes (2026-08-30).

## 2. Identidade, sessoes e autorizacao

- [x] 2.1 Mapear `auth/*` (login, OTP, troca de senha, logout, sessoes): campos validados, regras de bloqueio (tentativas, primeiro acesso), e a maquina de estados do login (senha valida -> codigo gerado -> codigo validado -> token); verificar contra `xano-workspace/api/conecta_rh_autenticacao/`. **Feito:** seção 1 do documento, incluindo ciclo de vida de sessões.
- [x] 2.2 Mapear o modelo de autorizacao por perfil (Admin/RH/Gestor/Colaborador) e por escopo (departamento, propriedade do registro), incluindo os casos onde o acesso e negado por padrao; verificar contra uma amostra representativa de endpoints em pelo menos 3 dominios diferentes. **Feito:** seção 2, amostra de 4 domínios (férias, colaboradores, documentos, ponto); autorização confirmada como duplicada por endpoint, não centralizada.

## 3. Colaboradores, cargos, departamentos e ponto

- [x] 3.1 Mapear cadastro de colaborador, vinculo profissional/historico e vinculo de gestor com vigencia: campos obrigatorios, validacoes de dominio (tipo_contrato, nivel, status) e o que cada alteracao registra em `historico_profissional`; verificar contra `xano-workspace/api/conecta_rh_colaboradores/` e `conecta_rh_departamentos/`. **Feito:** seção 3.
- [x] 3.2 Mapear registro de ponto e correcao: a maquina de estados (Aberto/Completo/Ajustado), quem pode solicitar/decidir uma correcao, e o calculo de horas trabalhadas; verificar contra `xano-workspace/api/conecta_rh_ponto/`. **Feito:** seção 4.

## 4. Ferias, ausencias e desligamento

- [x] 4.1 Mapear o ciclo de vida de ferias e ausencias (status, decisores autorizados, verificacao de conflito); verificar contra `xano-workspace/api/conecta_rh_ferias/` e `conecta_rh_ausencias/`. **Feito:** seção 5.
- [x] 4.2 Mapear o fluxo de desligamento (imediato e aviso previo), incluindo a decisao registrada em design.md de conectarh.gestao sobre conclusao manual em vez de automatica; verificar contra `xano-workspace/api/conecta_rh_desligamentos/`. **Feito:** seção 6.

## 5. Documentos

- [x] 5.1 Mapear o ciclo de vida de documento (status, tipos incluindo holerite/informe_rendimentos, vencimento, substituicao, pendencias solicitadas pelo RH) e as regras de acesso ao arquivo; verificar contra `xano-workspace/api/conecta_rh_documentos/`. **Feito:** seção 7.

## 6. Banco de horas, delegacao e regras contratuais

- [x] 6.1 Mapear banco de horas (ledger append-only, regra de elegibilidade por tipo de contrato) e delegacao temporaria de aprovacao; verificar contra os endpoints correspondentes em `conecta_rh_ponto` e `conecta_rh_gestao_de_usuarios`. **Feito:** seção 8; confirmado que a delegação não é consumida por nenhum fluxo de aprovação de terceiros (gap registrado).
- [x] 6.2 Mapear instrumento normativo e regra_override: maquinas de estado, bloqueio de autoaprovacao, exigencias para instrumentos coletivos e a logica de versionamento (regra vigente encerrada, nunca sobrescrita); verificar contra os endpoints em `conecta_rh_colaboradores` relacionados a `instrumentos_normativos` e `regras_override`. **Feito:** seção 9; confirmado que `regra_contrato`/`regra_aplicada` não têm API (motor de resolução ainda pendente).

## 7. Avaliacao e desenvolvimento

- [x] 7.1 Mapear ciclos de avaliacao, avaliacoes/respostas e contestacao; verificar contra os endpoints `ciclos_avaliacao`, `avaliacoes` e `contestacoes_avaliacao`. **Feito:** seção 10.
- [x] 7.2 Mapear metas (com trilha de check-in), PDI, reconhecimento/feedback (regra de visibilidade automatica) e pesquisa de clima (desenho de anonimato); verificar contra os endpoints correspondentes, citando a garantia estrutural de anonimato de `resposta_clima`. **Feito:** seção 11.

## 8. Experiencia do colaborador e conteudo

- [x] 8.1 Mapear central de solicitacoes, comunicados internos, FAQ, calendario organizacional, organograma, busca global, catalogos e parametros protegidos; verificar contra os endpoints correspondentes em `conecta_rh_colaboradores`. **Feito:** seção 12; organograma e busca global confirmados como implementados (ao contrário da suposição inicial da tarefa).
- [x] 8.2 Mapear a auditoria obrigatoria: quais acoes sao auditadas hoje e quais campos cada evento registra; verificar contra as ocorrencias de `db.add auditoria` no codigo. **Feito:** seção 13, incluindo lista de lacunas (endpoints que alteram estado sem auditar).

## 9. Consolidacao

- [x] 9.1 Revisar o documento completo contra a lista de dominios do indice (tarefa 1.1), marcando explicitamente qualquer dominio ou regra nao coberta como "nao mapeado" em vez de omitir; verificar que nenhuma secao do indice fica sem conteudo correspondente. **Feito:** todas as 13 seções do índice têm conteúdo; adicionada subseção final "Lacunas de escopo conhecidas" consolidando os 4 gaps estruturais encontrados (motor de regras contratuais, cancelamento de pendência, consumo de delegação, conclusão de onboarding).
