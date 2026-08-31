# Regras de Negócio — ConectaRH

**Data do levantamento:** 2026-08-30
**Fonte de verdade:** código publicado em `xano-workspace/` (tabelas em `xano-workspace/table/*.xs`, endpoints em `xano-workspace/api/**/*.xs`). Cada regra abaixo referencia o arquivo de origem para conferência direta.
**Natureza deste documento:** é um retrato do estado do código na data acima, não um documento vivo sincronizado automaticamente. Recomenda-se revisá-lo após mudanças relevantes no backend. Lacunas conhecidas são marcadas explicitamente como "não mapeado" em vez de omitidas.

## Índice

1. [Identidade e autenticação](#1-identidade-e-autenticação)
2. [Modelo de autorização (perfil × escopo)](#2-modelo-de-autorização-perfil--escopo)
3. [Colaboradores, vínculo profissional, cargos e departamentos](#3-colaboradores-vínculo-profissional-cargos-e-departamentos)
4. [Ponto e correção de ponto](#4-ponto-e-correção-de-ponto)
5. [Férias e ausências](#5-férias-e-ausências)
6. [Desligamento](#6-desligamento)
7. [Documentos](#7-documentos)
8. [Banco de horas e delegação de aprovação](#8-banco-de-horas-e-delegação-de-aprovação)
9. [Instrumentos normativos e regras de override](#9-instrumentos-normativos-e-regras-de-override)
10. [Avaliação de desempenho e contestação](#10-avaliação-de-desempenho-e-contestação)
11. [Metas, PDI, reconhecimento e pesquisa de clima](#11-metas-pdi-reconhecimento-e-pesquisa-de-clima)
12. [Central de solicitações, comunicados, FAQ, calendário e catálogos](#12-central-de-solicitações-comunicados-faq-calendário-e-catálogos)
13. [Auditoria](#13-auditoria)

---

## 1. Identidade e autenticação

### 1.1 Entidades e campos-chave

- `user`: `id`, `email` (único, trim|lower), `senha` (sensível/privado), `senha_primeiro_acesso` (bool, default true), `otp_codigo` (máx. 6, privado), `otp_expira_em` (privado), `otp_tentativas` (default 0, privado), `nome`, `perfil` (enum: `Admin`/`RH`/`Colaborador`/`Gestor`, default `Colaborador`), `ativo`, `ultimo_acesso` (`xano-workspace/table/user.xs`).
- `colaborador`: vinculado via `user_id` (índice único); relevantes aqui `nivel`, `nivel_desde`, `departamento_id`, `status` (`xano-workspace/table/colaborador.xs`).
- `sessao`: `id`, `user_id`, `expira_em`, `revogada_em`, `dispositivo`, `endereco_ip`, `ativa` (default true); índices em `user_id` e `(user_id, ativa)` (`xano-workspace/table/sessao.xs`).

### 1.2 Regras de validação

- `auth/login`: `email` (filtro email, trim|lower) e `password` obrigatórios (`xano-workspace/api/conecta_rh_autenticacao/auth/login_POST.xs`).
- `auth/otp/validar`: `email` (trim|lower) e `codigo` (trim, máx. 6) obrigatórios (`xano-workspace/api/conecta_rh_autenticacao/auth/otp_validar_POST.xs`).
- `auth/otp/reenviar`: `email` apenas; exige desafio OTP pendente (`otp_codigo != null`) (`xano-workspace/api/conecta_rh_autenticacao/auth/otp_reenviar_POST.xs`).
- `auth/senha` (PATCH): `senha_atual`, `nova_senha` e `confirmar_senha` (8-64 caracteres); devem coincidir entre si, `senha_atual` deve bater via `security.check_password`, e a nova senha deve ser diferente da atual (`xano-workspace/api/conecta_rh_autenticacao/auth/senha_PATCH.xs`).
- `auth/sessoes/{id}/encerrar`: a sessão deve pertencer ao chamador (`sessao.user_id == auth.id`) e estar `ativa` (`xano-workspace/api/conecta_rh_autenticacao/auth/sessoes/id/encerrar_POST.xs`).
- Todos os endpoints autenticados exigem `auth = "user"` e revalidam que o usuário ainda existe e está `ativo == true` (`xano-workspace/api/conecta_rh_autenticacao/auth/me_GET.xs`, `logout_POST.xs`, `minhas_sessoes_GET.xs`, `senha_PATCH.xs`).

### 1.3 Máquina de estados (login → OTP → token)

1. **`POST auth/login`**: busca `user` por e-mail; retorna erro genérico "E-mail ou senha inválidos" se usuário nulo ou `ativo == false` (sem enumeração de usuários); valida senha via `security.check_password` (mesmo erro genérico em caso de divergência). Em sucesso, gera OTP de 6 dígitos (`security.random_number` 100000-999999), grava em `user.otp_codigo` com `otp_expira_em = now+300s` e zera `otp_tentativas`; envia o código via template dinâmico SendGrid; se o envio falhar, retorna erro `standard` e não prossegue; audita `codigo_acesso_gerado` (nunca grava o código) (`xano-workspace/api/conecta_rh_autenticacao/auth/login_POST.xs`).
2. **`POST auth/otp/reenviar`**: exige `otp_codigo != null`; regenera código/expiração/tentativas e reenvia (`xano-workspace/api/conecta_rh_autenticacao/auth/otp_reenviar_POST.xs`).
3. **`POST auth/otp/validar`**: exige usuário ativo e desafio pendente; bloqueia após 5 tentativas falhas (`otp_tentativas < 5`, senão `toomanyrequests`, forçando novo login); bloqueia código expirado (`otp_expira_em > now`); em código errado incrementa `otp_tentativas` e audita `login_codigo_invalido` (falha). Em sucesso: limpa `otp_codigo`/`otp_expira_em`/`otp_tentativas`, atualiza `ultimo_acesso`, emite token (`security.create_auth_token`, `extras={perfil}`, `expiration=3600`), cria `sessao` (`expira_em=now+3600s`, `ativa=true`), audita `login_sucesso` (`xano-workspace/api/conecta_rh_autenticacao/auth/otp_validar_POST.xs`).
4. **`PATCH auth/senha`**: grava nova senha e `senha_primeiro_acesso=false`; audita `troca_senha`. Vários endpoints de negócio (ex.: `ferias/aprovar`, `minhas_ferias`) exigem adicionalmente `senha_primeiro_acesso == false` antes de permitir a ação (`xano-workspace/api/conecta_rh_autenticacao/auth/senha_PATCH.xs`, `xano-workspace/api/conecta_rh_ferias/ferias/id/aprovar_POST.xs`).

### 1.4 Sessões — ciclo de vida

- **Criação**: uma linha `sessao` por OTP validado com sucesso, `ativa=true`, `expira_em=now+3600s`; nenhum limite de sessões concorrentes observado no código (`xano-workspace/api/conecta_rh_autenticacao/auth/otp_validar_POST.xs`).
- **Logout** (`auth/logout`): encerra a sessão `ativa` mais recente do chamador (`ativa=false, revogada_em=now`); audita `logout`. O próprio código comenta que isso é uma aproximação de "sessão atual" — o token permanece criptograficamente válido até expirar naturalmente (1h) em endpoints que não checam a tabela `sessao` (`xano-workspace/api/conecta_rh_autenticacao/auth/logout_POST.xs`).
- **Revogação pontual** (`auth/sessoes/{id}/encerrar`): só revoga sessão do próprio chamador; rejeita sessão de terceiros (`accessdenied`) e sessão já inativa (`inputerror`) (`xano-workspace/api/conecta_rh_autenticacao/auth/sessoes/id/encerrar_POST.xs`).
- **Revogação em massa** (`auth/sessoes/encerrar_outras`): revoga todas as sessões ativas exceto a mais recente; audita `encerrar_outras_sessoes` com contagem, só se > 0 revogadas (`xano-workspace/api/conecta_rh_autenticacao/auth/sessoes/encerrar_outras_POST.xs`).
- **Listagem** (`auth/minhas_sessoes`): retorna todas as sessões (ativas e encerradas) do chamador, mais recentes primeiro (`xano-workspace/api/conecta_rh_autenticacao/auth/minhas_sessoes_GET.xs`).

### 1.5 O que é auditado

`codigo_acesso_gerado`, `login_codigo_invalido`, `login_sucesso`, `troca_senha`, `logout`, `encerrar_sessao`, `encerrar_outras_sessoes` (fontes acima). **Não auditado:** reenvio de OTP (`otp_reenviar_POST.xs` não grava em `auditoria`) — não mapeado.

---

## 2. Modelo de autorização (perfil × escopo)

### 2.1 Padrão comum de verificação de identidade/perfil

Todo endpoint autorizado recarrega o chamador via `db.get user { field_name="id", field_value=$auth.id }`, checa `!= null` (senão `unauthorized`) e `ativo == true` (senão `unauthorized`), e normaliza `perfil` com `|trim|to_upper` antes de comparar a literais como `"RH"`, `"ADMIN"`, `"GESTOR"` (`xano-workspace/api/conecta_rh_ferias/ferias/id/aprovar_POST.xs`, `xano-workspace/api/conecta_rh_colaboradores/colaboradores/id_GET.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id_GET.xs`, `xano-workspace/api/conecta_rh_ponto/correcoes_ponto/id/aprovar_POST.xs`).

### 2.2 Tabela de autorização (perfil × ação) — amostra representativa

| Ação | Admin | RH | Gestor | Colaborador | Evidência |
|---|---|---|---|---|---|
| Aprovar/listar todas as férias | sim | sim | não | não | `precondition ($perfil_decisor == "RH" || $perfil_decisor == "ADMIN")` (`xano-workspace/api/conecta_rh_ferias/ferias/id/aprovar_POST.xs`, `ferias_GET.xs`) |
| Ver/gerenciar próprias férias | sim | sim | sim | sim | filtro por `colaborador_id == colaborador_autenticado.id` (`xano-workspace/api/conecta_rh_ferias/minhas_ferias_GET.xs`) |
| Consultar qualquer colaborador | sim | sim | não | não | `precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")` (`xano-workspace/api/conecta_rh_colaboradores/colaboradores/id_GET.xs`) |
| Ver/listar próprios documentos | sim | sim | sim | sim | escopo por `colaborador_id` do token (`xano-workspace/api/conecta_rh_documentos/meus_documentos_GET.xs`) |
| Consultar documento por id | sim (qualquer) | sim (qualquer) | somente próprio | somente próprio | `$acesso_administrativo` OU `$acesso_proprietario` (`xano-workspace/api/conecta_rh_documentos/documentos/id_GET.xs`) |
| Aprovar correção de ponto | sim | sim | somente do próprio departamento gerenciado | não | ver escopo de departamento abaixo (`xano-workspace/api/conecta_rh_ponto/correcoes_ponto/id/aprovar_POST.xs`) |

### 2.3 Escopo de departamento

Para um Gestor agir sobre um colaborador, o código primeiro localiza o `colaborador` do chamador via `user_id`, depois localiza um `departamento` onde `departamento.gestor_colaborador_id == colaborador_autenticado.id`, e então compara `colaborador.departamento_id` alvo com o id desse departamento — um join de dois saltos, não um campo "gestor de" armazenado diretamente no colaborador (`xano-workspace/api/conecta_rh_ponto/correcoes_ponto/id/aprovar_POST.xs`). Esse é o único padrão de escopo por departamento encontrado na amostra de ferias/colaboradores/documentos/ponto.

### 2.4 Escopo de propriedade ("dono do registro")

Padrão: localizar `colaborador` por `user_id == auth.id`, exigir `status != "DESLIGADO"`, e então filtrar/comparar `registro.colaborador_id == colaborador_autenticado.id` — como filtro de query (endpoints de listagem) ou como flag booleana combinada via OR com acesso administrativo (endpoints de detalhe) (`xano-workspace/api/conecta_rh_ferias/minhas_ferias_GET.xs`, `xano-workspace/api/conecta_rh_documentos/meus_documentos_GET.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id_GET.xs`).

### 2.5 Comportamento padrão quando nenhuma condição é atendida

Negação explícita em todos os casos amostrados: um `precondition` que barra o conjunto de condições autorizadas (ex.: `precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")` ou `precondition ($acesso_administrativo || $acesso_proprietario)`) falha com `error_type = "accessdenied"` e mensagem em português — não há fallthrough implícito observado (`xano-workspace/api/conecta_rh_ferias/ferias_GET.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id_GET.xs`, `xano-workspace/api/conecta_rh_ponto/correcoes_ponto/id/aprovar_POST.xs`).

### 2.6 Centralizado vs. duplicado

A lógica de autorização é **duplicada por endpoint**: o mesmo bloco (recarregar usuário, checar `ativo`, normalizar `perfil`, comparar literais) é reescrito de forma independente em cada domínio amostrado — nenhum endpoint chama uma função compartilhada. Existe um helper genérico de RBAC em `xano-workspace/function/getting_started_template/role_based_access_control.xs`, mas é boilerplate do template inicial do Xano (usa uma hierarquia de papéis genérica `admin`/`member` que não corresponde a `user.perfil`) e não é referenciado por nenhum endpoint do ConectaRH — presente como template não integrado.

---

## 3. Colaboradores, vínculo profissional, cargos e departamentos

### 3.1 Entidades e campos-chave

- **colaborador**: campos obrigatórios `nome` (2-120), `email_pessoal`, `cpf` (11), `nivel` (enum `l1`-`l5`), `telefone`, `logradouro`, `numero`, `bairro`, `cargo_id`, `departamento_id`, `tipo_contrato` (enum `CLT`/`PJ`/`ESTAGIO`/`APRENDIZ`/`TEMPORARIO`/`OUTRO`), `salario`, `carga_horaria_semanal`, `status` (enum `Ativo`/`Ferias`/`Afastado`/`Desligado`). CPF e `user_id` têm índice único. Campos bancários (`banco`, `agencia`, `conta`, `digito`, `tipo_conta` enum `corrente`/`poupanca`) são opcionais (`xano-workspace/table/colaborador.xs`).
- **historico_profissional**: snapshot por período (`colaborador_id`, `cargo_id`, `departamento_id`, `nivel?`, `salario`, `tipo_contrato`, `carga_horaria_semanal`, `data_inicio`, `data_fim?`, `tipo_alteracao` enum `admissao`/`promocao`/`alteracao_departamento`/`alteracao_salarial`/`alteracao_cargo`/`alteracao_contratual`/`desligamento`, `motivo_alteracao?`, `user_id`) (`xano-workspace/table/historico_profissional.xs`).
- **historico_gestor_departamento**: `departamento_id`, `colaborador_id`, `data_inicio`, `data_fim?`, `definido_por_user_id` (`xano-workspace/table/historico_gestor_departamento.xs`).
- **cargo**: `nome` (único, 2-100), `descricao?`, `salario_base?`, `ativo?=true` (`xano-workspace/table/cargo.xs`).
- **departamento**: `nome` (único, 2-80), `descricao?`, `ativo?=true`, `gestor_colaborador_id?` (`xano-workspace/table/departamento.xs`).

### 3.2 Regras de validação

- `colaboradores_POST`: só RH; CPF único; e-mail pessoal único; `cargo_id`/`departamento_id` devem existir e estar `ativo`; `tipo_contrato` normalizado contra o enum exato; `nivel` normalizado contra `l1`-`l5`; `nivel_desde = data_admissao` (`xano-workspace/api/conecta_rh_colaboradores/colaboradores_POST.xs`).
- `colaboradores/{id}` PATCH: só RH; altera apenas dados pessoais/endereço; CPF e e-mail pessoal únicos (exceto o próprio registro) (`xano-workspace/api/conecta_rh_colaboradores/colaboradores/id_PATCH.xs`).
- `colaboradores/{id}/vinculo` PATCH: só RH; bloqueia colaborador `DESLIGADO`; `data_inicio >= data_admissao`; cargo/departamento devem existir e estar ativos; `tipo_contrato`/`nivel` validados contra os enums; `tipo_alteracao` validado, mas **exclui explicitamente "desligamento"** deste endpoint (`xano-workspace/api/conecta_rh_colaboradores/colaboradores/id/vinculo_PATCH.xs`).
- `departamentos/{id}/gestor` PATCH: departamento deve estar ativo; colaborador selecionado deve ter `status == ATIVO`, pertencer ao mesmo `departamento_id`, ter `user_id` vinculado e conta ativa com `perfil == GESTOR`; bloqueia se já for o gestor vigente (`xano-workspace/api/conecta_rh_departamentos/departamentos/id/gestor_PATCH.xs`).
- `cargos`/`departamentos` (POST/PATCH/status): nome único; alteração de status isolada dos demais campos (`xano-workspace/api/conecta_rh_cargos/`, `xano-workspace/api/conecta_rh_departamentos/`).

### 3.3 Máquina de estados

- `colaborador.status`: `Ativo | Ferias | Afastado | Desligado` — a transição completa não está definida nestes arquivos; `vinculo_PATCH` apenas bloqueia edição quando já `DESLIGADO`, mas nenhum endpoint lido nesta rodada grava `status="Desligado"` diretamente (isso ocorre no fluxo de desligamento — ver seção 6) — não mapeado aqui.
- Cada `vinculo_PATCH` encerra o `historico_profissional` aberto (`data_fim = data_inicio` nova) e cria um novo registro com `data_fim=null`; se não havia histórico, `tipo_alteracao` é forçado para `"admissao"` (`xano-workspace/api/conecta_rh_colaboradores/colaboradores/id/vinculo_PATCH.xs`).
- `gestor_PATCH` encerra o vínculo aberto em `historico_gestor_departamento` (`data_fim="now"`) e cria um novo com `data_fim=null` (`xano-workspace/api/conecta_rh_departamentos/departamentos/id/gestor_PATCH.xs`).

### 3.4 Tabela de autorização (perfil × ação)

| Ação | Perfil permitido |
|---|---|
| Criar colaborador | RH |
| Listar/consultar colaborador por id | RH, ADMIN |
| Atualizar dados pessoais | RH |
| Atualizar vínculo profissional | RH |
| Ver/editar próprio perfil e dados bancários | qualquer colaborador autenticado, só o próprio registro |
| Criar/editar cargo, alterar status | ADMIN, RH |
| Criar/editar departamento, alterar status | ADMIN, RH |
| Definir gestor de departamento | RH, ADMIN |
| Organograma (`organograma_GET`) | qualquer usuário autenticado ativo |
| Busca global (`colaboradores/buscar`) | qualquer usuário autenticado; GESTOR restrito ao próprio departamento gerenciado |

(`xano-workspace/api/conecta_rh_colaboradores/colaboradores_POST.xs`, `colaboradores/id_PATCH.xs`, `colaboradores/id/vinculo_PATCH.xs`, `meu_perfil_colaborador_GET.xs`, `meu_perfil_colaborador_PATCH.xs`, `meus_dados_bancarios_PATCH.xs`, `xano-workspace/api/conecta_rh_cargos/`, `xano-workspace/api/conecta_rh_departamentos/departamentos/id/gestor_PATCH.xs`, `xano-workspace/api/conecta_rh_departamentos/organograma_GET.xs`, `xano-workspace/api/conecta_rh_colaboradores/colaboradores/buscar_GET.xs`)

### 3.5 O que é auditado

`alterar_cadastro_colaborador` (`colaboradores/id_PATCH.xs`); evento com `acao=$tipo_historico`, `valor_anterior`/`valor_novo` e `justificativa=motivo_alteracao` (`vinculo_PATCH.xs`); `atualizar_dados_bancarios` (`meus_dados_bancarios_PATCH.xs`); `definir_gestor_departamento` (`gestor_PATCH.xs`). **Não auditado:** criação de colaborador (`colaboradores_POST.xs`) e endpoints de cargo/departamento — não mapeado.

---

## 4. Ponto e correção de ponto

### 4.1 Entidades e campos-chave

- **registro_ponto**: `colaborador_id`, `data?`, `hora_entrada?`, `inicio_intervalo?`, `fim_intervalo?`, `hora_saida?`, `horas_trabalhadas?`, `horas_extras?`, `status` (enum `Aberto`/`Completo`/`Incompleto`/`Ajustado`), `observacao?`; índice único composto `(colaborador_id, data)` (`xano-workspace/table/registro_ponto.xs`).
- **correcao_ponto**: `registro_ponto_id`, `colaborador_id`, `campo` (enum `hora_entrada`/`inicio_intervalo`/`fim_intervalo`/`hora_saida`), `valor_original?`, `valor_solicitado`, `justificativa` (5-1000), `status?=pendente` (enum `pendente`/`aprovada`/`rejeitada`), `decidido_por_user_id?`, `data_decisao?`, `motivo_decisao?` (`xano-workspace/table/correcao_ponto.xs`).

### 4.2 Regras de validação

- `ponto/marcar`: exige colaborador `ATIVO`; usa a data de hoje para localizar/criar o registro do dia (índice único evita duplicidade); marcações seguem ordem estrita entrada → início intervalo → fim intervalo → saída, cada uma condicionada ao estado dos campos anteriores; erro `inputerror` se todos os 4 marcadores já existem (`xano-workspace/api/conecta_rh_ponto/ponto/marcar_POST.xs`).
- `ponto/{id}/solicitar_correcao`: colaborador só solicita correção do próprio registro; `campo` validado contra o enum; bloqueia solicitação duplicada quando já existe correção `pendente` para o mesmo registro+campo; `valor_original` é lido do campo atual no momento da solicitação (`xano-workspace/api/conecta_rh_ponto/ponto/id/solicitar_correcao_POST.xs`).
- `correcoes_ponto/{id}/aprovar` e `/rejeitar`: exigem `status == "pendente"` (`xano-workspace/api/conecta_rh_ponto/correcoes_ponto/id/aprovar_POST.xs`, `rejeitar_POST.xs`).

### 4.3 Máquina de estados

`pendente → aprovada` (via `correcoes_ponto/{id}/aprovar`) ou `pendente → rejeitada` (via `.../rejeitar`); ambas exigem status atual `pendente`, gravam `decidido_por_user_id` e `data_decisao`; sem transição de volta (`xano-workspace/table/correcao_ponto.xs`).
- **Quem solicita**: o próprio colaborador dono do registro.
- **Quem decide**: RH, ADMIN, ou o Gestor cujo `departamento.gestor_colaborador_id` corresponde ao departamento do colaborador da correção.
- **Efeito da aprovação**: dentro de `db.transaction`, aplica `valor_solicitado` no campo correspondente de `registro_ponto`; se os 4 marcadores estiverem presentes, recalcula `horas_trabalhadas` e seta `status="Ajustado"`; senão, apenas seta `status="Ajustado"` sem recalcular.
- **Efeito da rejeição**: não altera `registro_ponto`; grava `status="rejeitada"`, `motivo_decisao`, `decidido_por_user_id`, `data_decisao`.
(`xano-workspace/api/conecta_rh_ponto/correcoes_ponto/id/aprovar_POST.xs`, `rejeitar_POST.xs`)

### 4.4 Cálculo de horas

- Na marcação de saída: `horas_trabalhadas = ((now - hora_entrada) - (fim_intervalo - inicio_intervalo)) / 3600000` (ms → horas) (`xano-workspace/api/conecta_rh_ponto/ponto/marcar_POST.xs`).
- No recálculo pós-aprovação de correção, mesma fórmula usando `hora_saida - hora_entrada - (fim_intervalo - inicio_intervalo)` (`xano-workspace/api/conecta_rh_ponto/correcoes_ponto/id/aprovar_POST.xs`).
- `horas_extras` existe no schema, mas nenhum endpoint lido o calcula ou grava — não mapeado.

### 4.5 Tabela de autorização (perfil × ação)

| Ação | Perfil permitido |
|---|---|
| Marcar ponto | Próprio colaborador, status `ATIVO` |
| Ver próprio espelho de ponto | Qualquer colaborador autenticado |
| Listar ponto de outro colaborador | RH, ADMIN |
| Solicitar correção | Próprio colaborador dono do registro |
| Aprovar/rejeitar correção | RH, ADMIN, ou Gestor do departamento do colaborador |
| Listar correções pendentes | RH/ADMIN (todas); Gestor (só do seu departamento) |
| Ver próprias correções | Próprio colaborador |

(`xano-workspace/api/conecta_rh_ponto/ponto/marcar_POST.xs`, `meu_ponto_GET.xs`, `ponto_GET.xs`, `ponto/id/solicitar_correcao_POST.xs`, `correcoes_ponto/id/aprovar_POST.xs`, `rejeitar_POST.xs`, `correcoes_ponto_GET.xs`, `minhas_correcoes_ponto_GET.xs`)

### 4.6 O que é auditado

`solicitar_correcao_ponto`, `aprovar_correcao_ponto` (com `valor_anterior`/`valor_novo`), `rejeitar_correcao_ponto` (com `justificativa`). **Não auditado:** `ponto/marcar` não grava evento em `auditoria` — não mapeado.

---

## 5. Férias e ausências

### 5.1 Entidades e campos-chave

- **ferias**: `id`, `colaborador_id`, `data_solicitacao`, `data_inicio`, `data_fim`, `quantidade_dias`, `status` (enum default `Pendente`: `Pendente`/`Aprovada`/`Rejeitada`/`Cancelada`/`Concluida`), `observacao_colaborador`, `observacao_rh`, `decidido_por_user_id`, `data_decisao` (`xano-workspace/table/ferias.xs`).
- **ausencia**: `id`, `colaborador_id`, `tipo` (enum sem default: `Falta`/`Atestado`/`Afastamento`/`Licenca`/`Outro`), `data_inicio`, `data_fim`, `motivo`, `comprovante`, `status` (enum sem default: `Pendente`/`Aprovada`/`Rejeitada`/`Registrado`), `observacao` (`xano-workspace/table/ausencia.xs`).

### 5.2 Regras de validação

- Férias — criação: `data_inicio`, `data_fim`, `quantidade_dias` (1-30); exige colaborador `ATIVO` e senha já trocada; `data_fim >= data_inicio`; bloqueia se já existir solicitação `Pendente` do mesmo colaborador (`xano-workspace/api/conecta_rh_ferias/ferias/solicitacoes_POST.xs`).
- Férias — edição: só o dono, só enquanto `Pendente`, `data_fim >= data_inicio` (`xano-workspace/api/conecta_rh_ferias/ferias/id_PATCH.xs`).
- Ausência — criação: `tipo` validado contra os 5 valores exatos; `motivo` (5-1000); `data_fim >= data_inicio`; `comprovante` opcional, salvo como `private`; exige colaborador `ATIVO` (`xano-workspace/api/conecta_rh_ausencias/ausencias_POST.xs`).
- Ausência — edição: mesmas validações; só dono, só enquanto `Pendente` (`xano-workspace/api/conecta_rh_ausencias/ausencias/id_PATCH.xs`).
- Ausência — rejeição: `observacao` obrigatória (5-1000) (`xano-workspace/api/conecta_rh_ausencias/ausencias/id/rejeitar_POST.xs`).
- Exclusão física de ausência é permanentemente bloqueada (`precondition (false)`) — nenhum perfil pode excluir (`xano-workspace/api/conecta_rh_ausencias/ausencias/id_DELETE.xs`).

### 5.3 Máquina de estados

**Férias**: `Pendente → Aprovada` (RH/ADMIN); `Pendente → Rejeitada` (RH/ADMIN); `Pendente → Cancelada` (dono, colaborador não desligado). Todas exigem status atual `Pendente`. Transição para `Concluida` não mapeada — não encontrado em nenhum endpoint lido (`xano-workspace/api/conecta_rh_ferias/ferias/id/aprovar_POST.xs`, `rejeitar_POST.xs`, `cancelar_POST.xs`).

**Ausência**: `Pendente → Aprovada` (RH/ADMIN); `Pendente → Rejeitada` (RH/ADMIN, exige justificativa); `Aprovada → Registrado` (RH/ADMIN, confirma o registro administrativo). Não há endpoint de cancelamento — não mapeado (`xano-workspace/api/conecta_rh_ausencias/ausencias/id/aprovar_POST.xs`, `rejeitar_POST.xs`, `registrar_POST.xs`).

### 5.4 Verificação de conflito de férias

`ferias/{id}/verificar_conflito` (GET, somente informativo, não bloqueia a decisão): calcula (1) antecedência em dias; (2) período aquisitivo cumprido (comparado a `regra_contrato.periodo_aquisitivo_meses` ativa para o `tipo_contrato` do colaborador); (3) férias sobrepostas (`Aprovada`) do mesmo colaborador; (4) ausências sobrepostas (`Aprovada`) do mesmo colaborador; (5) colegas de férias no período — contagem de colegas do mesmo departamento com férias `Aprovada` sobrepondo o período, e tamanho da equipe. Acesso restrito a RH, ADMIN ou GESTOR (`xano-workspace/api/conecta_rh_ferias/ferias/id/verificar_conflito_GET.xs`).

### 5.5 Tabela de autorização (perfil × ação)

| Ação | Perfis permitidos | Escopo |
|---|---|---|
| Solicitar/editar/cancelar férias | qualquer perfil com colaborador ativo | só o dono |
| Aprovar/rejeitar férias | RH, ADMIN | sem restrição de departamento no código |
| Verificar conflito de férias | RH, ADMIN, GESTOR | — |
| Listar todas as férias | RH, ADMIN | — |
| Solicitar ausência | qualquer perfil com colaborador ativo | só o dono |
| Aprovar/rejeitar/registrar ausência | RH, ADMIN | sem restrição de departamento no código |
| Excluir ausência | ninguém (bloqueado) | — |

Não há verificação de escopo por departamento do aprovador em nenhum endpoint de férias/ausências — diferente do fluxo de desligamento, que possui essa checagem para o Gestor (ver seção 6) — não mapeado.

### 5.6 O que é auditado

`aprovar_ferias`, `cancelar_ferias`, `rejeitar_ferias`; `aprovar_ausencia`, `registrar_ausencia`, `rejeitar_ausencia` (com `justificativa`). **Não auditado:** criação/edição (POST/PATCH) e consultas GET — não mapeado.

---

## 6. Desligamento

### 6.1 Entidades e campos-chave

**solicitacao_desligamento**: `id`, `colaborador_id`, `solicitante_user_id`, `origem` (enum `funcionario`/`gestor`), `tipo_desligamento` (enum `imediato`/`aviso_previo`), `data_prevista`, `data_efetiva`, `dias_aviso`, `motivo_solicitacao`, `status` (enum default `pendente`: `pendente`/`agendado`/`em_analise`/`rejeitada`/`cancelada`/`concluido`), `responsavel_rh_user_id`, `data_inicio_analise`, `decidido_por_user_id`, `data_decisao`, `motivo_decisao`, `cancelado_por_user_id`, `data_cancelamento`, `motivo_cancelamento`, `data_conclusao` (`xano-workspace/table/solicitacao_desligamento.xs`).

### 6.2 Regras de validação

- Criação: `tipo_desligamento` validado; se `imediato`, `dias_aviso` deve ser `0`; se `aviso_previo`, `dias_aviso > 0`; colaborador-alvo deve estar `ATIVO`; colaborador comum só solicita o próprio desligamento; gestor só solicita de colaborador cujo departamento tenha `gestor_colaborador_id` igual ao seu; bloqueia se já existir solicitação `pendente`/`em_analise`/`agendado` para o colaborador; `motivo_solicitacao` (5-1000) (`xano-workspace/api/conecta_rh_desligamentos/solicitacoes_desligamento_POST.xs`).
- Aprovação: exige status `em_analise`; colaborador ainda `ATIVO` e com `user_id` vinculado; `motivo_decisao` (5-1000); `data_efetiva` obrigatória (`xano-workspace/api/conecta_rh_desligamentos/solicitacoes_desligamento/id/aprovar_POST.xs`).
- Rejeição: exige status `em_analise`; `motivo_decisao` obrigatório (5-1000) (`.../rejeitar_POST.xs`).
- Cancelamento: exige status `pendente`; só o `solicitante_user_id` original; `motivo_cancelamento` obrigatório (5-1000) (`.../cancelar_POST.xs`).
- Conclusão manual: exige status `agendado` e `data_efetiva <= now` (`.../concluir_POST.xs`).

### 6.3 Máquina de estados

`pendente → em_analise` (RH, via `iniciar_analise`) → `em_analise → rejeitada` (RH) ou `em_analise → aprovar` (RH), que se ramifica por `tipo_desligamento`:
- **imediato**: `em_analise → concluido` diretamente na mesma transação — desliga o colaborador (`status="Desligado"`), desativa a conta (`user.ativo=false`), encerra o `historico_profissional` aberto e cria novo registro `tipo_alteracao: "desligamento"`.
- **aviso_previo**: `em_analise → agendado` (sem desligar ainda).

`pendente → cancelada` (só pelo solicitante original, só enquanto `pendente`).

`agendado → concluido`: **não é automático por padrão** — o endpoint `concluir_POST.xs` é acionado manualmente pelo RH. Existe uma rotina automática como arquivo de task (`xano-workspace/task/concluir_desligamentos_agendados.xs`), mas não pode ser publicada porque o plano Xano do workspace não inclui Background Tasks; o endpoint manual reproduz a mesma transação como solução temporária (`xano-workspace/api/conecta_rh_desligamentos/solicitacoes_desligamento/id/concluir_POST.xs`).

(`xano-workspace/api/conecta_rh_desligamentos/solicitacoes_desligamento/id/aprovar_POST.xs`, `rejeitar_POST.xs`, `cancelar_POST.xs`, `concluir_POST.xs`, `iniciar_analise_POST.xs`)

### 6.4 Tabela de autorização (perfil × ação)

| Ação | Perfis permitidos | Escopo |
|---|---|---|
| Criar solicitação | COLABORADOR (de si mesmo) ou GESTOR (do próprio departamento) | — |
| Iniciar análise / Aprovar / Rejeitar / Concluir | RH exclusivamente | — |
| Cancelar | COLABORADOR ou GESTOR | só o próprio `solicitante_user_id` |
| Consultar por id | RH (qualquer); solicitante (própria); GESTOR responsável pelo departamento do colaborador-alvo | — |
| Listar fila | RH exclusivamente | — |

### 6.5 O que é auditado

`aprovar_desligamento_imediato`, `aprovar_desligamento_agendado` (com `justificativa`), `rejeitar_desligamento` (com `justificativa`), `cancelar_desligamento` (com `justificativa`), `concluir_desligamento_agendado`. **Não auditado:** `iniciar_analise` e criação da solicitação — não mapeado.

---

## 7. Documentos

### 7.1 Entidades e campos-chave

**`documento`**: `id`, `colaborador_id`→colaborador, `tipo` (enum: `rg`, `cpf`, `cin`, `cnh`, `ctps`, `aso_admissional`, `laudo_deficiencia`, `certificado_profissional`, `comprovante_residencia`, `comprovante_escolaridade`, `registro_profissional`, `documentacao_migratoria`, `certificado_reservista`, `documentacao_responsavel_legal`, `outro`, `holerite`, `informe_rendimentos`), `nome_documento`, `numero_documento`, `estado_de_emissao`, `data_emissao`, `data_validade`, `observacao`, `status` (enum: `pendente_analise`, `aprovado`, `rejeitado`, `vencido`, `substituido`, `arquivado`, default `pendente_analise`), `estado_verificacao` (enum: `enviado`, `em_verificacao`, `liberado`, `bloqueado`, default `enviado`), `ultimo_alerta_dias`, `hash_arquivo`, `documento_substituido_id`→documento, `motivo_bloqueio`, `imagem_frente`, `imagem_verso`, `arquivo_url`, `ativo` (default true) (`xano-workspace/table/documento.xs`).

**`pendencia_documento`**: `id`, `colaborador_id`, `tipo_documento` (mesmo enum, exceto `holerite`/`informe_rendimentos`), `prazo` (data), `observacao`, `status` (enum: `pendente`, `atendida`, `cancelada`, default `pendente`), `solicitado_por_user_id`→user, `atendida_por_documento_id`→documento, `atendida_em` (`xano-workspace/table/pendencia_documento.xs`).

**`evento_sst`** (SST/ASO, tratado no mesmo api_group): `id`, `colaborador_id`, `tipo` (enum: `aso_admissional`, `aso_periodico`, `aso_demissional`, `aso_mudanca_funcao`, `pcmso_prazo`, `outro_sst`), `resultado` (enum: `apto`, `inapto`, `apto_com_restricao`), `data_exame`, `data_validade`, `medico_responsavel`, `documento_url`, `observacao_operacional`, `registrado_por_user_id`. Comentário no schema explicita que o campo nunca deve conter diagnóstico ou registro clínico livre, apenas resultado/prazos operacionais (`xano-workspace/table/evento_sst.xs`).

### 7.2 Regras de validação

- `documentos_POST`: exige `colaborador_id`, `tipo`, `nome_documento` (2-150 caracteres); requer ao menos um de `imagem_frente`, `imagem_verso` ou `arquivo_url`; `data_validade` não pode ser anterior a `data_emissao`; bloqueia cadastro para colaborador com `status` `DESLIGADO`; `tipo` validado contra a lista exata do enum (`xano-workspace/api/conecta_rh_documentos/documentos_POST.xs`).
- `holerite`/`informe_rendimentos` só podem ser anexados por RH/ADMIN; nesse caso o documento nasce com `status=aprovado` e `data_validade=null` (não vencem) (`xano-workspace/api/conecta_rh_documentos/documentos_POST.xs`).
- `documento_substituido_id`, se informado, deve pertencer ao mesmo colaborador e estar `aprovado` ou `vencido` (`xano-workspace/api/conecta_rh_documentos/documentos_POST.xs`).
- PATCH `documentos/{id}`: só sobre documento `ativo`; preserva imagens/`arquivo_url`/observação quando omitidos; exige que ao menos um de imagem_frente/imagem_verso/arquivo_url permaneça após a edição; não aceita `tipo` `holerite`/`informe_rendimentos` (`xano-workspace/api/conecta_rh_documentos/documentos/id_PATCH.xs`).
- `rejeitar`: `observacao` obrigatória (mín. 5 caracteres) como justificativa (`xano-workspace/api/conecta_rh_documentos/documentos/id/rejeitar_POST.xs`).
- `pendencias_documento_POST`: `prazo` deve ser data futura; não permite `tipo_documento` `holerite`/`informe_rendimentos`; bloqueia pendência duplicada aberta do mesmo tipo para o colaborador (`xano-workspace/api/conecta_rh_documentos/pendencias_documento_POST.xs`).
- `eventos_sst_POST`: `tipo` e `resultado` validados contra enum exato; `data_exame` obrigatória (`xano-workspace/api/conecta_rh_documentos/eventos_sst_POST.xs`).

### 7.3 Máquina de estados

- `pendente_analise` → `aprovado` (via `documentos/{id}/aprovar`, só a partir de `pendente_analise`) ou → `rejeitado` (via `documentos/{id}/rejeitar`, só a partir de `pendente_analise`, exige observação) (`xano-workspace/api/conecta_rh_documentos/documentos/id/aprovar_POST.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id/rejeitar_POST.xs`).
- `aprovado`/`vencido` → `substituido`: automático, dentro da transação de `documentos_POST`, quando um novo documento é criado com `documento_substituido_id` apontando para o anterior (`xano-workspace/api/conecta_rh_documentos/documentos_POST.xs`).
- `aprovado` → `vencido`: processado por `documentos/processar_vencimentos` (disparo manual por RH/ADMIN — sem Background Tasks no plano Xano), quando `data_validade` já passou; dispara e-mails de alerta em 30/15/7/0 dias, idempotentes via `ultimo_alerta_dias` (`xano-workspace/api/conecta_rh_documentos/documentos/processar_vencimentos_POST.xs`).
- `rejeitado`/`vencido`/`substituido` → `arquivado` (via `documentos/{id}/arquivar`, zera `ativo`, encerrando edição) (`xano-workspace/api/conecta_rh_documentos/documentos/id/arquivar_POST.xs`).
- Exclusão física é bloqueada incondicionalmente para todos os perfis — só arquivamento (`xano-workspace/api/conecta_rh_documentos/documentos/id_DELETE.xs`).
- Pendência: `pendente` → `atendida` (automático, quando um documento do mesmo `tipo` é cadastrado, seta `atendida_por_documento_id`/`atendida_em`); transição para `cancelada` **não mapeada** — nenhum endpoint de cancelamento encontrado (`xano-workspace/api/conecta_rh_documentos/documentos_POST.xs`, `xano-workspace/table/pendencia_documento.xs`).

### 7.4 Regras de acesso ao arquivo

`documentos/{id}/arquivo` (GET) retorna `arquivo_url`: RH/ADMIN acessam qualquer documento; demais usuários só se forem o colaborador dono (`colaborador.user_id == usuário`) e o colaborador não estiver `DESLIGADO` (`xano-workspace/api/conecta_rh_documentos/documentos/id/arquivo_GET.xs`). Mesma regra self/RH/ADMIN em `documentos/{id}` GET/PATCH e `meus_documentos` (restrito ao próprio colaborador) (`xano-workspace/api/conecta_rh_documentos/documentos/id_GET.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id_PATCH.xs`, `xano-workspace/api/conecta_rh_documentos/meus_documentos_GET.xs`). Gestor não tem acesso a documentos nem a `evento_sst` — exclusão explícita no comentário do endpoint de SST (`xano-workspace/api/conecta_rh_documentos/colaboradores/id/eventos_sst_GET.xs`). Imagens são armazenadas com `access = "private"` via `storage.create_image` (`xano-workspace/api/conecta_rh_documentos/documentos_POST.xs`).

### 7.5 Tabela de autorização (perfil × ação)

| Ação | Colaborador (próprio) | RH/ADMIN | Gestor |
|---|---|---|---|
| Cadastrar documento próprio | Sim (exceto holerite/informe_rendimentos) | Sim (qualquer colaborador, todos os tipos) | não mapeado |
| Cadastrar holerite/informe_rendimentos | Não | Sim | não mapeado |
| Ver/baixar arquivo próprio | Sim | Sim (qualquer) | Não |
| Listar todos os documentos | Não | Sim | não mapeado |
| Aprovar/Rejeitar/Arquivar | Não | Sim | não mapeado |
| Excluir documento | Ninguém (bloqueado) | Ninguém (bloqueado) | Ninguém |
| Criar pendência | Não | Sim | Não |
| Listar pendências (todas) | Não | Sim | não mapeado |
| Ver próprias pendências | Sim | Sim (via listagem geral) | não mapeado |
| Registrar/ver evento_sst | Ver próprio; não registra | Sim | Não |

(`xano-workspace/api/conecta_rh_documentos/documentos_POST.xs`, `xano-workspace/api/conecta_rh_documentos/documentos_GET.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id/aprovar_POST.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id/rejeitar_POST.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id/arquivar_POST.xs`, `xano-workspace/api/conecta_rh_documentos/documentos/id_DELETE.xs`, `xano-workspace/api/conecta_rh_documentos/pendencias_documento_POST.xs`, `xano-workspace/api/conecta_rh_documentos/pendencias_documento_GET.xs`, `xano-workspace/api/conecta_rh_documentos/eventos_sst_POST.xs`, `xano-workspace/api/conecta_rh_documentos/colaboradores/id/eventos_sst_GET.xs`)

### 7.6 O que é auditado

Registros em `auditoria` (`user_id`, `acao`, `recurso`, `registro_id`, `justificativa`, `resultado`) são gravados em: aprovação de documento (`aprovar_documento`) (`xano-workspace/api/conecta_rh_documentos/documentos/id/aprovar_POST.xs`), rejeição de documento (`rejeitar_documento`, inclui `justificativa`) (`xano-workspace/api/conecta_rh_documentos/documentos/id/rejeitar_POST.xs`), solicitação de pendência (`solicitar_documento_pendente`) (`xano-workspace/api/conecta_rh_documentos/pendencias_documento_POST.xs`) e registro de evento SST (`registrar_evento_sst`) (`xano-workspace/api/conecta_rh_documentos/eventos_sst_POST.xs`). Cadastro (`documentos_POST`), atualização (PATCH), arquivamento e `processar_vencimentos` **não** gravam entrada em `auditoria` — não mapeado.

---

## 8. Banco de horas e delegação de aprovação

### 8.1 Entidades e campos-chave

- **banco_horas_lancamento**: `colaborador_id`, `tipo` (enum `credito`/`debito`), `horas` (decimal, mín. 0.01), `origem`, `instrumento_normativo_id?`, `data_lancamento`, `data_expiracao?`, `registrado_por_user_id`, `observacao?`. O comentário de cabeçalho declara explicitamente o padrão append-only (`xano-workspace/table/banco_horas_lancamento.xs`).
- **delegacao_aprovacao**: `titular_user_id`, `substituto_user_id`, `escopo` (enum `ferias`/`ausencia`/`documento`/`desligamento`/`correcao_ponto`/`solicitacao_rh`/`todas`), `data_inicio`, `data_fim`, `motivo`, `criado_por_user_id`, `cancelada_em?`, `cancelada_por_user_id?` (`xano-workspace/table/delegacao_aprovacao.xs`).

### 8.2 Regras de validação

- Lançamento: `tipo` restrito a `credito`/`debito`; `horas` mín. 0.01; exige `regra_contrato` ativa para o `tipo_contrato` do colaborador com `permite_banco_horas == true`, senão bloqueia com `inputerror` (`xano-workspace/api/conecta_rh_ponto/banco_horas/lancar_POST.xs`).
- Delegação: `escopo` validado contra enum; `data_fim >= data_inicio`; substituto precisa estar ativo; **bloqueio de autodelegação**: `titular_id_final != substituto_user_id` (`xano-workspace/api/conecta_rh_gestao_de_usuarios/delegacoes_POST.xs`).

### 8.3 Padrão append-only e cálculo de saldo

Não há estados no banco de horas — cada lançamento é imutável desde a criação; não existem endpoints de edição/exclusão sobre `banco_horas_lancamento` em todo o workspace (confirmado). O saldo **não é armazenado**: é sempre recalculado somando `credito` e subtraindo `debito` sobre todos os lançamentos do colaborador (`xano-workspace/api/conecta_rh_ponto/colaboradores/id/banco_horas_GET.xs`, replicado em `meu_banco_horas_GET.xs`).

### 8.4 Delegação — estados e escopo

`criada` → (opcional) `cancelada` via `cancelada_em`/`cancelada_por_user_id`; sem reversão de cancelamento; a vigência é lida pelas datas `data_inicio`/`data_fim`, mas nenhum endpoint lido consome a delegação para de fato substituir um aprovador em outro fluxo (ferias/aprovar, correcoes_ponto/aprovar etc. não fazem lookup em `delegacao_aprovacao`) — apenas CRUD de criação/listagem/cancelamento foi encontrado; o consumo efetivo da delegação em fluxos de terceiros é **não mapeado** (`xano-workspace/api/conecta_rh_gestao_de_usuarios/delegacoes/id/cancelar_POST.xs`).

### 8.5 Tabela de autorização (perfil × ação)

| Ação | Quem pode |
|---|---|
| Lançar banco de horas | RH ou ADMIN |
| Consultar banco de horas de outro colaborador | RH/ADMIN, o próprio colaborador, ou o Gestor da equipe do departamento |
| Consultar próprio banco de horas | Qualquer usuário autenticado vinculado a um colaborador |
| Criar delegação em nome próprio | Qualquer usuário ativo |
| Criar delegação em nome de outro titular | Apenas RH/ADMIN |
| Cancelar delegação | Titular, RH ou ADMIN |
| Listar próprias delegações | Qualquer usuário autenticado (titular ou substituto) |

(`xano-workspace/api/conecta_rh_ponto/banco_horas/lancar_POST.xs`, `colaboradores/id/banco_horas_GET.xs`, `meu_banco_horas_GET.xs`, `xano-workspace/api/conecta_rh_gestao_de_usuarios/delegacoes_POST.xs`, `delegacoes/id/cancelar_POST.xs`, `minhas_delegacoes_GET.xs`)

### 8.6 O que é auditado

`lancar_banco_horas` (com `valor_novo` = tipo:horas, `justificativa=origem`); `criar_delegacao_aprovacao`; `cancelar_delegacao_aprovacao`. Consultas de saldo (GET) não geram auditoria.

---

## 9. Instrumentos normativos e regras de override

### 9.1 Entidades e campos-chave

- **instrumento_normativo**: `tipo` (enum incl. `acordo_coletivo`, `convencao_coletiva`, `termo_aditivo`, `regime_especial`, `norma_legal`, `decisao_judicial`, `acordo_individual_autorizado`), `titulo`, `abrangencia_territorial`, `numero_solicitacao_mediador?`, `numero_registro_mte?`, `numero_processo_mte?`, `data_registro?`, `data_inicio`, `data_fim?`, `documento_url`, `hash_documento`, `status` (enum default `rascunho`: `rascunho`/`pendente_aprovacao`/`vigente`/`suspenso`/`expirado`/`revogado`/`rejeitado`), `criado_por_user_id`, `aprovado_por_user_id?`, `data_aprovacao?`, `instrumento_principal_id?` (`xano-workspace/table/instrumento_normativo.xs`).
- **regra_override**: `instrumento_normativo_id`, `parametro` (enum de parâmetros protegidos), `valor_anterior?`, `valor_novo`, `prioridade`, `abrangencia` (enum `empresa`/`estabelecimento`/`estado`/`municipio`/`departamento`/`cargo`/`tipo_contrato`/`categoria_profissional`/`colaborador`), escopo (`departamento_id?`/`cargo_id?`/`colaborador_id?`/`tipo_contrato?`/`estado?`/`municipio?`/`categoria_profissional?`), `data_inicio`, `data_fim?`, `tipo_aplicacao` (`futura`/`retroativa`, default `futura`), `versao?=1`, `ativo?=false`, `status` (enum default `rascunho`: `rascunho`/`pendente_aprovacao`/`aprovada`/`vigente`/`encerrada`/`suspensa`/`revogada`/`rejeitada`) (`xano-workspace/table/regra_override.xs`).
- `regra_contrato` e `regra_aplicada` existem como tabelas (parâmetros por `tipo_contrato`, e registro de aplicação de regra por processo), mas **não têm nenhum endpoint de API correspondente** em `xano-workspace/api/` — o motor de resolução de regras (aplicar override + regra de contrato a um colaborador/processo) não está exposto via API; isso é consistente com o Non-Goal registrado em `openspec/changes/conectarh.gestao/design.md` sobre as tarefas 4.11-4.13/4.17 ainda pendentes (`xano-workspace/table/regra_contrato.xs`, `xano-workspace/table/regra_aplicada.xs`).

### 9.2 Regras de validação

- Criação de instrumento: `tipo` validado contra o enum exato; apenas RH/ADMIN (`xano-workspace/api/conecta_rh_colaboradores/instrumentos_normativos_POST.xs`).
- Criação de override: exige `instrumento_normativo.status == "vigente"`; `parametro` validado contra `parametro_protegido`, bloqueando quando `nivel_protecao == "sem_override"`; `abrangencia` validada contra enum; `tipo_aplicacao == "retroativa"` exige `justificativa` preenchida (`xano-workspace/api/conecta_rh_colaboradores/regras_override_POST.xs`).

### 9.3 Máquina de estados

**instrumento_normativo**: `rascunho` →(`enviar_aprovacao`)→ `pendente_aprovacao` →(`aprovar`)→ `vigente` ou →(`rejeitar`)→ `rejeitado`; `vigente` →(`suspender`)→ `suspenso`; `vigente`/`suspenso` →(`revogar`)→ `revogado`. Estado `expirado` existe no enum mas nenhum endpoint transiciona para ele — não mapeado (`xano-workspace/api/conecta_rh_colaboradores/instrumentos_normativos/id/enviar_aprovacao_POST.xs`, `aprovar_POST.xs`, `rejeitar_POST.xs`, `suspender_POST.xs`, `revogar_POST.xs`).

**regra_override**: `rascunho` →(`enviar_aprovacao`)→ `pendente_aprovacao` →(`aprovar`)→ `vigente`. Estados `aprovada`, `encerrada`, `suspensa`, `revogada`, `rejeitada` existem no enum, mas só `encerrada` é efetivamente atingida (automaticamente, ao aprovar a substituta); não há endpoint `rejeitar`/`suspender`/`revogar` para override — não mapeado (`xano-workspace/api/conecta_rh_colaboradores/regras_override/id/enviar_aprovacao_POST.xs`, `aprovar_POST.xs`).

**Versionamento na aprovação de override** (transação): busca vigente anterior com mesmo `parametro`+`abrangencia`+escopo; se existir, dentro de `db.transaction`, é editada apenas para `status: "encerrada", ativo: false, data_fim: <data_inicio da nova>` (nunca reaproveitada como registro ativo), e a nova regra recebe `versao = anterior.versao + 1`, `status: "vigente"`, `ativo: true`. Ambas as operações e o registro de auditoria ocorrem na mesma transação (`xano-workspace/api/conecta_rh_colaboradores/regras_override/id/aprovar_POST.xs`).

**Bloqueio de autoaprovação** confirmado em ambos os fluxos: `precondition (registro.criado_por_user_id != usuario_autenticado.id)` — tanto para instrumento quanto para override (`xano-workspace/api/conecta_rh_colaboradores/instrumentos_normativos/id/aprovar_POST.xs`, `regras_override/id/aprovar_POST.xs`).

**Requisito para instrumentos coletivos**: para `tipo` em `acordo_coletivo`, `convencao_coletiva`, `termo_aditivo`, a aprovação exige `numero_solicitacao_mediador`, `numero_registro_mte`, `numero_processo_mte`, `data_registro` e `documento_url` todos preenchidos; sem isso, o instrumento não pode ir para `vigente` (`xano-workspace/api/conecta_rh_colaboradores/instrumentos_normativos/id/aprovar_POST.xs`).

### 9.4 Tabela de autorização (perfil × ação)

| Ação | Quem pode |
|---|---|
| Cadastrar/enviar/aprovar/rejeitar/suspender/revogar instrumento normativo | Somente RH ou ADMIN |
| Criar/enviar/aprovar regra_override | Somente RH ou ADMIN |
| Listar instrumentos/overrides | Qualquer usuário autenticado, sem filtro de perfil |

### 9.5 O que é auditado

Cadastro, aprovação, rejeição, suspensão e revogação de `instrumento_normativo` (com `justificativa` nas três últimas). **Exceção:** `enviar_aprovacao` de instrumento não grava auditoria. Para override: criação e aprovação são auditadas (aprovação registra `valor_anterior`/`valor_novo`); `enviar_aprovacao` de override também não audita.

---

## 10. Avaliação de desempenho e contestação

### 10.1 Entidades e campos-chave

- **ciclo_avaliacao**: `nome`, `descricao`, `data_inicio`, `data_checkin`, `data_fim`, `status` (enum default `planejamento`: `planejamento`/`em_andamento`/`fechamento`/`concluido`/`cancelado`), `criado_por_user_id`, `ativo` (`xano-workspace/table/ciclo_avaliacao.xs`).
- **avaliacao**: `colaborador_id` (avaliado), `user_id` (avaliador), `ciclo_avaliacao_id`, `relacao_avaliador` (enum `autoavaliacao`/`gestor`/`par`/`subordinado`/`rh`), `periodo_inicio/fim`, `nota`, `comentario`, `data_avaliacao`, `status` (enum default `pendente`: `pendente`/`em_andamento`/`enviada`/`cancelada`) (`xano-workspace/table/avaliacao.xs`).
- **resposta_avaliacao**: `avaliacao_id`, `competencia_avaliacao_id`, `nota` (1-5), `comentario`; índice único composto `(avaliacao_id, competencia_avaliacao_id)` (`xano-workspace/table/resposta_avaliacao.xs`).
- **competencia_avaliacao**: `nome`, `descricao`, `categoria` (enum `tecnica`/`comportamental`/`lideranca`/`valor_empresa`), `nivel` (enum `l1`-`l5`), `peso`, `ativo` (`xano-workspace/table/competencia_avaliacao.xs`).
- **contestacao_avaliacao**: `avaliacao_id`, `colaborador_id`, `motivo`, `status` (enum default `aberta`: `aberta`/`revisada`), `revisado_por_user_id`, `resposta_revisao`, `data_revisao` (`xano-workspace/table/contestacao_avaliacao.xs`).

### 10.2 Regras de validação

- Ciclo (POST): `nome` (máx. 100), `descricao` (máx. 500) (`xano-workspace/api/conecta_rh_colaboradores/ciclos_avaliacao_POST.xs`).
- Avaliação (POST): `relacao_avaliador` restrito ao enum; se `autoavaliacao`, o avaliador deve ser o próprio avaliado (`colaborador.user_id`) (`xano-workspace/api/conecta_rh_colaboradores/avaliacoes_POST.xs`).
- Resposta (POST): `nota` 1-5; avaliação deve estar `pendente`/`em_andamento`; competência deve existir; chamada repetida para a mesma competência atualiza em vez de duplicar (`xano-workspace/api/conecta_rh_colaboradores/avaliacoes/id/respostas_POST.xs`).
- Enviar (POST): avaliação deve pertencer ao chamador como avaliador, estar `pendente`/`em_andamento`, e ter ao menos 1 resposta; `nota` geral = média aritmética das respostas (`xano-workspace/api/conecta_rh_colaboradores/avaliacoes/id/enviar_POST.xs`).
- Contestar (POST): `motivo` (5-2000); avaliação deve estar `enviada`; chamador deve ser o avaliado (`xano-workspace/api/conecta_rh_colaboradores/avaliacoes/id/contestar_POST.xs`).
- Revisar (POST): `resposta_revisao` (5-2000); contestação deve estar `aberta` (`xano-workspace/api/conecta_rh_colaboradores/contestacoes_avaliacao/id/revisar_POST.xs`).

### 10.3 Máquina de estados

- **ciclo_avaliacao**: criado como `planejamento`. Nenhum endpoint transiciona para `em_andamento`/`fechamento`/`concluido`/`cancelado` — não mapeado.
- **avaliacao**: `pendente` → (primeiro `respostas_POST`) → `em_andamento` → (`enviar_POST`, exige ≥1 resposta) → `enviada` (terminal). `cancelada` existe no enum mas nenhum endpoint a define — não mapeado. Uma vez `enviada`, `respostas_POST` e `enviar_POST` rejeitam novas escritas.
- **contestacao_avaliacao**: `aberta` → (`revisar_POST`) → `revisada` (terminal; segunda revisão é rejeitada).

O enum `relacao_avaliador` (`autoavaliacao`/`gestor`/`par`/`subordinado`/`rh`) sugere feedback multi-fonte (estilo 360°), mas não existe um campo explícito "tipo 90/180/360" — não mapeado.

### 10.4 Tabela de autorização (perfil × ação)

| Ação | Perfil permitido |
|---|---|
| Criar ciclo | RH, ADMIN |
| Listar ciclos | Qualquer usuário autenticado |
| Atribuir avaliação (avaliador×avaliado) | RH, ADMIN |
| Registrar resposta / enviar avaliação | Somente o `user_id` designado como avaliador |
| Ver avaliação por id | RH/ADMIN sempre; avaliador sempre; avaliado somente se `enviada` |
| Contestar avaliação | Somente o colaborador avaliado, e somente se `enviada` |
| Listar/revisar contestações | RH, ADMIN |

### 10.5 O que é auditado

`atribuir_avaliacao`, `contestar_avaliacao`, `revisar_contestacao_avaliacao` (com `justificativa` = `resposta_revisao`), `enviar_avaliacao` (descrito no código como "decisão imutável em trilha de auditoria"). **Não auditado:** criação de ciclo, criação de respostas, e os endpoints GET — não mapeado.

---

## 11. Metas, PDI, reconhecimento e pesquisa de clima

### 11.1 Entidades e campos-chave

- **meta_avaliacao**: `ciclo_avaliacao_id`, `colaborador_id`, `titulo`, `descricao`, `indicador`, `valor_esperado`, `unidade_medida`, `peso`, `data_prazo`, `progresso_percentual`, `comentario_checkin`, `data_checkin_realizado`, `resultado_final`, `comentario_final`, `status` (enum default `planejada`: `planejada`/`em_andamento`/`concluida`/`cancelada`), `criado_por_user_id` (`xano-workspace/table/meta_avaliacao.xs`).
- **meta_checkin**: log append-only — `meta_avaliacao_id`, `registrado_por_user_id`, `progresso_percentual`, `comentario`, `dificuldades`, `evidencia`, `novo_prazo`; comentário no arquivo: "trilha completa... append-only. meta_avaliacao guarda só o check-in mais recente" (`xano-workspace/table/meta_checkin.xs`).
- **pdi**: `ciclo_avaliacao_id`, `colaborador_id`, `titulo`, `descricao`, `acao_desenvolvimento`, `responsavel_user_id`, `data_inicio/prazo`, `progresso_percentual`, `status` (enum default `planejado`: `planejado`/`em_andamento`/`concluido`/`cancelado`), `evidencia` (`xano-workspace/table/pdi.xs`).
- **reconhecimento**: `remetente_user_id`, `destinatario_colaborador_id`, `competencia_avaliacao_id`, `titulo`, `mensagem`, `visibilidade` (enum default `publico`: `publico`/`privado`), `status` (enum default `ativo`: `ativo`/`cancelado`/`moderado`), `moderado_por_user_id`, `motivo_moderacao` (`xano-workspace/table/reconhecimento.xs`).
- **pesquisa_clima**: `titulo`, `descricao`, `data_inicio`, `data_fim`, `minimo_respostas` (default 5), `criado_por_user_id`, `ativo` (`xano-workspace/table/pesquisa_clima.xs`).
- **pergunta_clima**: `pesquisa_clima_id`, `texto`, `ordem` (`xano-workspace/table/pergunta_clima.xs`).
- **resposta_clima**: `pergunta_clima_id`, `departamento_id` (nulável, capturado no momento da resposta), `nota` (1-5) — **zero colunas de identidade** (sem `colaborador_id`, sem `user_id`); comentário no arquivo: "não há como ligar uma linha desta tabela a uma pessoa específica, nem para RH/ADMIN" (`xano-workspace/table/resposta_clima.xs`).
- **resposta_clima_participacao**: `pergunta_clima_id`, `colaborador_id`, índice único no par — usado só para bloquear voto duplicado, nunca cruzado com `resposta_clima`; comentário: "nunca é cruzada com resposta_clima ... não compromete o anonimato" (`xano-workspace/table/resposta_clima_participacao.xs`).

### 11.2 Regras de validação

- Meta (POST): `peso`/`valor_esperado` limitados a 100; colaborador-alvo padrão é o próprio chamador, ou (se diferente) exige RH/ADMIN/GESTOR (`xano-workspace/api/conecta_rh_colaboradores/metas_POST.xs`).
- Check-in (POST): `progresso_percentual` 0-100; bloqueado se meta `concluida`/`cancelada` (`xano-workspace/api/conecta_rh_colaboradores/metas/id/checkin_POST.xs`).
- Concluir meta (POST): `resultado_final` máx. 100; bloqueado se já `concluida`/`cancelada` (`xano-workspace/api/conecta_rh_colaboradores/metas/id/concluir_POST.xs`).
- PDI progresso (POST): `progresso_percentual` 0-100; bloqueado se `concluido`/`cancelado`; define `status="concluido"` automaticamente quando `progresso_percentual >= 100`, senão `em_andamento` (`xano-workspace/api/conecta_rh_colaboradores/pdi/id/progresso_POST.xs`).
- Reconhecimento (POST): `titulo` máx. 100, `mensagem` máx. 1500; bloqueia autorreconhecimento (`xano-workspace/api/conecta_rh_colaboradores/reconhecimentos_POST.xs`).
- Pesquisa (POST): `data_fim >= data_inicio`; `minimo_respostas` mín. 2, default 5 (`xano-workspace/api/conecta_rh_colaboradores/pesquisas_clima_POST.xs`).
- Responder pergunta de clima (POST): `nota` 1-5; bloqueia resposta duplicada via `resposta_clima_participacao` antes de inserir (`xano-workspace/api/conecta_rh_colaboradores/perguntas_clima/id/responder_POST.xs`).

### 11.3 Máquina de estados

- **meta_avaliacao**: `planejada` → (qualquer check-in) → `em_andamento` → (`concluir_POST`) → `concluida`; `cancelada` existe no enum mas nenhum endpoint a define — não mapeado.
- **pdi**: `planejado` → (`progresso_POST`) → `em_andamento` ou, se `progresso_percentual >= 100`, direto para `concluido`; `cancelado` não é definido por nenhum endpoint — não mapeado.
- **reconhecimento**: `ativo` → (`moderar_POST`, RH/ADMIN, só se `ativo`) → `moderado` (terminal); `cancelado` existe no enum mas nunca é definido — não mapeado.
- **pesquisa_clima**: sem enum de status, só booleano `ativo` (true na criação); nenhum endpoint o desativa — não mapeado.

### 11.4 Tabela de autorização (perfil × ação)

| Ação | Perfil permitido |
|---|---|
| Criar meta para si | Qualquer colaborador autenticado |
| Criar meta para outro colaborador | RH, ADMIN, GESTOR |
| Registrar check-in de meta | Dono da meta ou RH/ADMIN |
| Ver trilha de check-ins | Dono, Gestor do departamento, ou RH/ADMIN |
| Concluir meta | RH, ADMIN, ou Gestor do departamento |
| Criar PDI | RH, ADMIN, GESTOR |
| Atualizar progresso de PDI | Próprio colaborador, `responsavel_user_id`, ou RH/ADMIN |
| Enviar reconhecimento | Qualquer colaborador (não a si mesmo) |
| Moderar reconhecimento | RH, ADMIN |
| Criar pesquisa / perguntas de clima | RH, ADMIN |
| Ver resultados agregados de clima | RH, ADMIN |
| Responder pergunta de clima | Qualquer colaborador (uma vez por pergunta) |

### 11.5 Reconhecimento — regra automática de visibilidade

Visibilidade não é escolhida pelo remetente: o sistema verifica se o remetente é o `gestor_colaborador_id` do departamento do destinatário; se sim, `visibilidade = "privado"` (pode conter conteúdo corretivo); caso contrário `visibilidade = "publico"` (deve ser só reconhecimento positivo, sujeito a moderação a posteriori) (`xano-workspace/api/conecta_rh_colaboradores/reconhecimentos_POST.xs`). Um registro privado só é visto por destinatário, remetente e RH/ADMIN.

### 11.6 Pesquisa de clima — desenho de anonimato

`resposta_clima` tem só `pergunta_clima_id`, `departamento_id`, `nota` — zero colunas de identidade. `resposta_clima_participacao` é uma tabela separada (`pergunta_clima_id`, `colaborador_id`, índice único no par) cujo único propósito é bloquear uma segunda resposta à mesma pergunta; nunca é cruzada com `resposta_clima`. A regra de um-voto-por-pessoa é aplicada em `perguntas_clima/id/responder_POST.xs`: consulta `resposta_clima_participacao` por um par (pergunta, colaborador) existente e usa `precondition` sobre `participacao_existente == null` antes de inserir ambas as linhas na mesma transação. A agregação de resultados também suprime qualquer grupo (departamento ou geral) com contagem de respostas abaixo de `pesquisa.minimo_respostas`, para evitar reidentificação por eliminação (`xano-workspace/api/conecta_rh_colaboradores/pesquisas_clima/id/resultados_GET.xs`).

### 11.7 O que é auditado

Nenhuma chamada `db.add auditoria` foi encontrada em nenhum endpoint desta seção (metas, pdi, reconhecimentos, pesquisas_clima, perguntas_clima) — incluindo `moderar_POST.xs`, que apesar de tratar uma ação de moderação **não** grava em `auditoria` (só persiste `reconhecimento.motivo_moderacao`/`moderado_por_user_id`) — não mapeado.

---

## 12. Central de solicitações, comunicados, FAQ, calendário e catálogos

### 12.1 Central de solicitações (`solicitacao_rh`)

Entidade: `colaborador_id`, `tipo` (enum `alteracao_cadastral`/`declaracao`/`documento_avulso`/`outra`), `descricao` (5-2000), `status` (enum default `recebida`: `recebida`/`em_analise`/`atendida`/`indeferida`), `decidido_por_user_id`, `justificativa_decisao` (máx. 1000), `data_decisao` (`xano-workspace/table/solicitacao_rh.xs`).

Máquina de estados: criada como `recebida`; `atender` e `indeferir` exigem status atual `recebida` ou `em_analise`, transicionando para `atendida` ou `indeferida` respectivamente. `indeferir` exige `justificativa_decisao` obrigatória (5-1000); em `atender` a justificativa é opcional (`xano-workspace/api/conecta_rh_colaboradores/solicitacoes/id/atender_POST.xs`, `.../solicitacoes/id/indeferir_POST.xs`).

Autorização: qualquer colaborador autenticado ativo (não `DESLIGADO`, senha já trocada) cria solicitação para si mesmo; só RH/ADMIN listam todas ou decidem (atender/indeferir) (`xano-workspace/api/conecta_rh_colaboradores/solicitacoes_POST.xs`, `solicitacoes_GET.xs`). Colaborador lê as próprias via `minhas_solicitacoes_GET.xs`, que também agrega as próprias `ferias` e `ausencia` na mesma resposta. Nota: `atender` não altera por si só o cadastro do colaborador — RH ainda precisa aplicar a mudança pelo fluxo normal de PATCH de colaborador (`xano-workspace/api/conecta_rh_colaboradores/solicitacoes/id/atender_POST.xs`).

Auditado: `criar_solicitacao_rh`, `atender_solicitacao_rh`, `indeferir_solicitacao_rh`.

### 12.2 Comunicados

Entidade: `titulo` (3-200), `conteudo` (5-5000), `publico_alvo` (enum `todos`/`departamento`/`perfil`), `departamento_id?`, `perfil_alvo?` (enum `Admin`/`RH`/`Colaborador`/`Gestor`), `data_inicio`, `data_fim?`, `publicado_por_user_id`, `ativo` (default true) (`xano-workspace/table/comunicado.xs`).

Validação: `publico_alvo` deve ser um valor exato do enum; `departamento_id` obrigatório quando `publico_alvo=="departamento"`; `perfil_alvo` obrigatório quando `publico_alvo=="perfil"`; `data_fim` (se presente) deve ser `>= data_inicio` (`xano-workspace/api/conecta_rh_colaboradores/comunicados_POST.xs`).

Autorização: só RH/ADMIN publicam ou listam todos os comunicados. Regra de visibilidade em `meus_comunicados_GET.xs`: o comunicado deve estar `ativo` e dentro da vigência (`data_inicio <= hoje` e `data_fim` nulo ou `>= hoje`), E (`publico_alvo=="todos"`) OU (`publico_alvo=="perfil"` e corresponde ao perfil do usuário) OU (`publico_alvo=="departamento"` e corresponde ao `departamento_id` do colaborador) (`xano-workspace/api/conecta_rh_colaboradores/meus_comunicados_GET.xs`).

Auditado: `publicar_comunicado`.

### 12.3 FAQ (`artigo_faq`)

Entidade: `categoria` (enum `ferias`/`ponto`/`documentos`/`politicas_internas`), `titulo` (máx. 200), `conteudo` (máx. 5000), `publicado_por_user_id`, `ativo` (default true) (`xano-workspace/table/artigo_faq.xs`).

Autorização: qualquer usuário autenticado lê artigos ativos (`artigos_faq_GET.xs`, filtrado `ativo==true`, ordenado por categoria). Só RH/ADMIN publicam (criam), com `categoria` validada contra o enum exato (`xano-workspace/api/conecta_rh_colaboradores/artigos_faq_POST.xs`). Nenhum endpoint de atualização/exclusão foi encontrado — não mapeado. **Não auditado:** criação de artigo FAQ, ao contrário de comunicados.

### 12.4 Calendário e feriados

Entidade `feriado`: `data`, `nome` (máx. 200), `abrangencia` (enum `nacional`/`estadual`/`municipal`, default `nacional`), `estado?`, `municipio?`, `ativo` (default true) (`xano-workspace/table/feriado.xs`).

`calendario_GET.xs` agrega: feriados ativos (visíveis a todos, sem filtro de perfil), mais `ferias` com `status=="Aprovada"` e `ausencia` com `status=="Aprovada"`, com escopo por departamento — RH/ADMIN veem todos os departamentos; GESTOR/COLABORADOR ficam restritos ao próprio `departamento_id` (`xano-workspace/api/conecta_rh_colaboradores/calendario_GET.xs`).

Autorização para gerenciar feriados: só RH/ADMIN; `abrangencia` validada contra o enum exato, com default `nacional` quando omitida (`xano-workspace/api/conecta_rh_colaboradores/feriados_POST.xs`). **Não auditado:** criação de feriado.

### 12.5 Catálogos

`catalogos_GET.xs` é um endpoint somente-leitura, aberto a qualquer usuário autenticado ativo, retornando listas estáticas de valores de enum espelhadas das tabelas/endpoints para uso em dropdowns do frontend — o próprio código documenta explicitamente que não é ele mesmo a fonte de validação, apenas um espelho das validações aplicadas em outros lugares (`xano-workspace/api/conecta_rh_colaboradores/catalogos_GET.xs`).

### 12.6 Parâmetros protegidos

Entidade `parametro_protegido`: `parametro` (enum de 15 configurações protegíveis, ex.: `horas_diarias`, `dias_ferias`, `permite_solicitacao_ferias`), `nivel_protecao` (enum `configuravel`/`configuravel_com_aprovacao`/`sem_override`), `descricao?`, índice único em `parametro` (`xano-workspace/table/parametro_protegido.xs`).

Autorização: só RH/ADMIN leem o catálogo (`xano-workspace/api/conecta_rh_colaboradores/parametros_protegidos_GET.xs`). A proteção efetiva é aplicada em `regras_override_POST.xs`: a criação de um `regra_override` é bloqueada com `accessdenied` se o `parametro_protegido.nivel_protecao == "sem_override"` correspondente; a criação de override é restrita a RH/ADMIN e nasce sempre como `status: "rascunho"`, `ativo: false` (ainda não em vigor) — ver seção 9 para o fluxo completo (`xano-workspace/api/conecta_rh_colaboradores/regras_override_POST.xs`).

### 12.7 Onboarding

Entidades: `onboarding` (`colaborador_id` único, `iniciado_por_user_id`, `data_inicio`, `status` enum `em_andamento`/`concluido`, default `em_andamento`) e `onboarding_item` (`onboarding_id`, `categoria` — 13 etapas fixas de checklist, `descricao`, `responsavel` enum `rh`/`colaborador`/`gestor`, `concluido` bool default false, `concluido_por_user_id?`, `concluido_em?`, `evidencia?` máx. 500) (`xano-workspace/table/onboarding.xs`, `xano-workspace/table/onboarding_item.xs`).

Criação: só RH/ADMIN; colaborador-alvo não pode estar `DESLIGADO` nem já ter um onboarding (um por colaborador); cria o `onboarding` mais exatamente 13 `onboarding_item` com `responsavel` fixo por categoria, dentro de uma transação (`xano-workspace/api/conecta_rh_colaboradores/colaboradores/id/onboarding_POST.xs`). Auditado como `iniciar_onboarding`.

Leitura: permitida a RH/ADMIN, ao próprio colaborador, ou ao Gestor do departamento do colaborador; retorna os itens mais o `percentual_concluido` calculado (`xano-workspace/api/conecta_rh_colaboradores/colaboradores/id/onboarding_GET.xs`).

Máquina de estados do item: `pendente` (`concluido:false`) → `concluido:true`; bloqueado se já concluído. Autorização por item é por `responsavel`: item `rh` exige perfil RH/ADMIN; item `colaborador` exige que o usuário autenticado seja o colaborador do onboarding; item `gestor` exige perfil GESTOR gerenciando o departamento do colaborador; RH/ADMIN sempre podem concluir em nome de qualquer responsável (supervisão) (`xano-workspace/api/conecta_rh_colaboradores/onboarding_item/id/concluir_POST.xs`). Auditado como `concluir_item_onboarding`. A transição do `onboarding.status` para `concluido` na conclusão de todos os itens **não foi encontrada** — não mapeado.

### 12.8 Organograma e busca global

Ambos **estão implementados**:
- Organograma (`organograma_GET.xs`): qualquer usuário autenticado ativo; retorna três listas planas (`departamentos` com `gestor_colaborador_id`, `cargos`, `colaboradores` limitados a id/nome/cargo_id/departamento_id) para o cliente montar a hierarquia; nenhum campo sensível exposto (`xano-workspace/api/conecta_rh_departamentos/organograma_GET.xs`).
- Busca global (`colaboradores/buscar_GET.xs`): qualquer usuário autenticado; `termo` (2-100); combina nome (icontains), CPF (exato), id/matrícula (exato), nome de cargo ou de departamento; GESTOR restrito ao próprio departamento gerenciado, demais perfis veem qualquer colaborador ativo; CPF é aceito como termo de busca mas nunca retornado nos resultados (`xano-workspace/api/conecta_rh_colaboradores/colaboradores/buscar_GET.xs`).

---

## 13. Auditoria

### 13.1 Esquema da tabela `auditoria`

`id`, `created_at` (privado), `user_id` (FK→user, nulável), `acao` (texto, obrigatório), `recurso` (texto, obrigatório), `registro_id` (nulável), `valor_anterior` (nulável), `valor_novo` (nulável), `justificativa` (nulável), `resultado` (nulável), `endereco_ip`, `identificador_sessao`, `rastreamento_id` (todos texto, nuláveis) (`xano-workspace/table/auditoria.xs`). **Nota:** `endereco_ip`, `identificador_sessao` e `rastreamento_id` existem no schema mas nunca são preenchidos por nenhuma chamada `db.add auditoria` encontrada em `xano-workspace/api/` — são colunas mortas hoje.

### 13.2 Ações auditadas por domínio

| Domínio | Ações auditadas |
|---|---|
| Auth | `codigo_acesso_gerado`, `login_codigo_invalido`, `login_sucesso`, `troca_senha`, `logout`, `encerrar_sessao`, `encerrar_outras_sessoes` |
| Colaboradores/cadastro | `alterar_cadastro_colaborador`, vínculo (`acao` dinâmico = `tipo_historico`), `atualizar_dados_bancarios` (com diff), `iniciar_onboarding`, `concluir_item_onboarding` |
| Férias | `aprovar_ferias`, `rejeitar_ferias`, `cancelar_ferias` |
| Ausências | `registrar_ausencia`, `aprovar_ausencia`, `rejeitar_ausencia` |
| Desligamento | `aprovar_desligamento_imediato`, `aprovar_desligamento_agendado`, `rejeitar_desligamento`, `cancelar_desligamento`, `concluir_desligamento_agendado` |
| Documentos | `aprovar_documento`, `rejeitar_documento`, `registrar_evento_sst`, `solicitar_documento_pendente` |
| Ponto / banco de horas | `lancar_banco_horas` (com diff), `aprovar_correcao_ponto` (com diff completo), `rejeitar_correcao_ponto`, `solicitar_correcao_ponto` |
| Instrumentos/override | `cadastrar_instrumento_normativo`, `aprovar_instrumento_normativo`, `rejeitar_instrumento_normativo`, `suspender_instrumento_normativo`, `revogar_instrumento_normativo`, `criar_regra_override`, `aprovar_regra_override` |
| Avaliação | `atribuir_avaliacao`, `enviar_avaliacao`, `contestar_avaliacao`, `revisar_contestacao_avaliacao`, `moderar_reconhecimento` |
| Comunicados/FAQ/Solicitações/Delegações/Usuários/Departamentos | `publicar_comunicado`, `criar_solicitacao_rh`, `atender_solicitacao_rh`, `indeferir_solicitacao_rh`, `criar_delegacao_aprovacao`, `cancelar_delegacao_aprovacao`, `definir_gestor_departamento`, `alterar_status_usuario` (com diff), `alterar_perfil_usuario` (com diff) |
| Parâmetros protegidos | Nenhum — só existe endpoint de leitura (`parametros_protegidos_GET.xs`); não há endpoint de mutação para auditar |

(fontes: ver seções 1-12 acima, cada uma citando o arquivo específico por ação)

### 13.3 Lacunas identificadas

Endpoints que alteram estado mas **não** gravam em `auditoria`:

- **Documentos**: exclusão (`documentos/id_DELETE.xs`), arquivamento (`documentos/id/arquivar_POST.xs`), criação (`documentos_POST.xs`), atualização (`documentos/id_PATCH.xs`), `processar_vencimentos_POST.xs` (job de vencimento em lote).
- **Férias/Ausências**: `ausencias/id_DELETE.xs`, `ausencias/id_PATCH.xs`, `ferias/id_PATCH.xs`, `ferias/solicitacoes_POST.xs` (criação).
- **Desligamento**: `solicitacoes_desligamento_POST.xs` (criação), `.../id/iniciar_analise_POST.xs`.
- **Cargos**: todo o domínio — `cargos_POST.xs`, `cargos/id_PATCH.xs`, `cargos/id/status_PATCH.xs`.
- **Departamentos**: `departamentos_POST.xs`, `departamentos/id_PATCH.xs`, `departamentos/id/status_PATCH.xs` (só `gestor_PATCH.xs` é auditado).
- **Gestão de usuários**: `usuarios_POST.xs` (criação), `usuarios/id_PATCH.xs` (só alteração de status/perfil é auditada).
- **Colaboradores**: `colaboradores_POST.xs` (criação), `meu_perfil_colaborador_PATCH.xs` (autoedição).
- **Avaliação/desenvolvimento**: `ciclos_avaliacao_POST.xs`, `avaliacoes/id/respostas_POST.xs`, todo o domínio de metas (`metas_POST.xs`, `checkin_POST.xs`, `concluir_POST.xs`), todo o domínio de PDI (`pdi_POST.xs`, `progresso_POST.xs`), `reconhecimentos_POST.xs` (criação — só a moderação é auditada), `enviar_aprovacao_POST.xs` de instrumento e de override.
- **Ponto**: `ponto/marcar_POST.xs` (a própria marcação de ponto).
- **Comunicados/FAQ**: `artigos_faq_POST.xs` (ao contrário de `comunicados_POST.xs`).

---

## Lacunas de escopo conhecidas (fora deste levantamento)

Por decisão registrada em `design.md` deste change, este documento cobre apenas domínios com backend já implementado. Ficam explicitamente fora, por não terem endpoints de API publicados:

- **Motor de resolução de regras contratuais** (tarefas 4.11-4.13/4.17 do change `conectarh.gestao`): as tabelas `regra_contrato` e `regra_aplicada` existem, mas não há endpoint que as consuma — ver seção 9.1.
- **Cancelamento de pendência de documento**: a tabela `pendencia_documento` tem status `cancelada` no enum, mas nenhum endpoint de cancelamento foi encontrado — ver seção 7.3.
- **Consumo efetivo de `delegacao_aprovacao`** nos fluxos de aprovação de terceiros (férias, correção de ponto etc.): só CRUD da delegação em si foi encontrado, nenhum fluxo de aprovação faz lookup nela — ver seção 8.4.
- **Conclusão de `onboarding`**: a transição do `onboarding.status` para `concluido` ao concluir o último item não foi encontrada — ver seção 12.7.
