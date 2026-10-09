# Evidências — rotinas e fluxos (Parte 2)

Verificações por HTTP contra o workspace Xano, em 08/10/2026, com a conta de administração do projeto. Contas pelo papel, sem e-mail nem token. Ids de registro são de dados de teste.

## 3.20 Status do ciclo de avaliação

| Cenário | Requisição | Esperado | Obtido |
|---|---|---|---|
| Pular etapa | `PATCH ciclos_avaliacao/{id}/status` `concluido` num ciclo em planejamento | Recusa | 400 |
| Meta em ciclo em planejamento | `POST metas` | Recusa | 400 |
| Sequência válida | `em_andamento`, `fechamento`, `concluido` | Aceita | 200 nas três |
| Meta em ciclo em andamento | `POST metas` | Aceita | 200 |
| Voltar de `fechamento` a `em_andamento` | `PATCH .../status` | Recusa | 400 |
| Ciclo inexistente | `PATCH .../status` | Não encontrado | 404 |

`avaliacoes POST` recebeu a mesma exigência de ciclo `em_andamento`, mas não foi exercitado por HTTP (precisa de um avaliador e de um colaborador avaliado).

## 3.21 Encerrar pesquisa de clima

| Cenário | Requisição | Esperado | Obtido |
|---|---|---|---|
| Encerrar | `POST pesquisas_clima/{id}/encerrar` | Aceita | 200 |
| Encerrar de novo | idem | Recusa | 400 |
| Responder depois de encerrar | `POST perguntas_clima/{id}/responder` | Recusa | 400 |

## 3.22 Onboarding conclui sozinho

Num onboarding de 13 itens, concluir os itens 1 a 12 devolveu `onboarding_concluido = false`; o item 13 devolveu `true`, e a leitura seguinte mostrou `status = concluido`.

## 3.27 Retenção de documentos

| Cenário | Esperado | Obtido |
|---|---|---|
| Regra de retenção de 365 dias a partir da emissão e documento emitido em 10/01/2025 | `retencao_ate = 2026-01-10` | `2026-01-10` |
| `GET documentos/retencao_vencida` | Lista só leitura, sem arquivo, link, imagem nem número | 200, campos `id`, `colaborador_id`, `tipo`, `nome_documento`, `status`, `retencao_ate` |

## 3.15 e 3.16 Gestor decide férias e delegação vigente

Contas pelo papel: *Admin* (solicitante, com colaborador no departamento "rh"), *Gestor de teste* (conta de Colaborador promovida a Gestor só para o teste) e *titular* (gestor original do departamento). Perfis e gestor do departamento foram restaurados no fim.

Em `ferias/{id}/aprovar|rejeitar` a autorização é conferida **antes** do estado da solicitação, então "403" significa sem escopo e "400 somente pendentes" significa que a autorização passou. Foi usado um período já aprovado do Admin, porque a conta atingiu o máximo de períodos e não foi possível criar novas solicitações.

| Cenário | Esperado | Obtido |
|---|---|---|
| Gestor do próprio departamento aprova férias da equipe (primeira rodada, solicitação pendente) | Aprovada | 200 |
| Gestor do próprio departamento, período já decidido | Passa da autorização | 400 "Somente solicitações pendentes" |
| Gestor de outra equipe, sem delegação (aprovar e rejeitar) | Negado | 403 nos dois |
| Delegação vigente com escopo `documento` | Ignorada | 403 |
| Delegação vigente com escopo `ferias` | Passa da autorização | 400 "Somente solicitações pendentes" |
| Delegação de `ferias` cancelada | Negado | 403 |

`correcoes_ponto/{id}/rejeitar`:

| Cenário | Esperado | Obtido |
|---|---|---|
| Gestor de outra equipe, sem delegação | Negado | 403 |
| Substituto com delegação `correcao_ponto` vigente | Aceita | 200 |
| Delegação cancelada | Negado | 403 |
| Gestor do próprio departamento | Aceita | 200 |
| Admin aprova a própria correção | Negado | 403 |
| Auditoria da decisão por delegação | Registra o titular | `decisao por delegacao do titular user_id=<titular>` na justificativa |

**Não verificado por HTTP:** o substituto concluindo (200) uma solicitação de **férias** pendente, o Gestor decidindo as próprias férias (a conta de Gestor de teste não tem contrato que permita pedir férias) e a delegação com `data_fim` já passada (a criação recusa datas passadas). A autorização é o mesmo bloco nos quatro endpoints, e o 200 de decisão foi confirmado nas correções de ponto e na primeira rodada de férias.

## 3.18 e 3.19 Rotina diária e status operacional

`POST rotinas/processar_diarias` (RH e Admin) chama a função `ConectaHR/processar_transicoes_diarias` com `aplicar = true`; `GET status_operacional` chama a mesma função com `aplicar = false`, então a contagem pendente e a aplicada saem da mesma regra.

| Cenário | Esperado | Obtido |
|---|---|---|
| `status_operacional` antes: 1 férias encerrada, 1 ponto aberto de dia anterior e 2 colaboradores como `Ferias`/`Afastado` sem período vigente | Contagens pendentes | `ferias_concluidas = 1`, `ponto_para_incompleto = 1`, `colaboradores_para_ativo = 2` |
| Primeira execução | Mesmas contagens aplicadas | Idênticas às pendentes |
| `status_operacional` logo depois | Tudo zerado | Zerado |
| Segunda execução | Contagens zeradas | Zeradas |
| Afastamento aprovado cobrindo hoje, colaborador `Ativo` | `colaboradores_para_afastado = 1` no pendente e na execução; o colaborador vira `Afastado` e segue no organograma | Igual; segunda execução zerada |
| Colaborador e Gestor chamam a rotina | Negado | 403 nos dois |
| Gestor chama `status_operacional` | Negado | 403 |
| Auditoria | `processar_rotinas_diarias` com as contagens | Registrada a cada execução |

**Não exercitados por HTTP, por falta de dados de teste:** o desligamento agendado vencido (concluiria uma conta de teste), o instrumento `vigente` vencido, `Ativo → Ferias` (nenhuma férias aprovada em andamento) e o colaborador `Desligado` com férias ou afastamento terminado. O último vale por construção: a rotina só altera colaboradores `Ativo`, `Ferias` ou `Afastado`.

**Fuso horário:** a rotina compara datas em UTC, como o resto do sistema. À noite no Brasil (depois das 21h) o "hoje" da rotina já é o dia seguinte; uma ausência que termina no dia local já não é considerada vigente. Isso apareceu no teste, e foi preciso criar a ausência com fim no dia seguinte.

## 3.23 Organograma com colaboradores de férias e afastados

Com colaboradores reais de teste nos status `Ferias` (1) e `Afastado` (1): ambos apareceram em `organograma`, e os 2 `Desligado` ficaram de fora. O filtro de `aniversariantes` é o mesmo, mas nenhum desses colaboradores faz aniversário neste mês, então não foi observado na resposta.

## 3.24 e 3.25 Equipe e dashboard do Gestor

| Cenário | Esperado | Obtido |
|---|---|---|
| Colaborador e Admin chamam `minha_equipe` | Negado | 403 |
| Gestor chama `minha_equipe` | Só a própria equipe (10 pessoas), sem campo sensível | 200; campos `id`, `nome`, `cargo_id`, `departamento_id`, `nivel`, `tipo_contrato`, `data_admissao`, `status`, `ferias_proximas`, `ausencias`, `ponto_hoje`; nenhum CPF, salário, dado bancário, contato, endereço ou data de nascimento |
| Ausências na equipe | Só tipo, período e status | `tipo`, `data_inicio`, `data_fim`, `status` |
| Gestor chama `central_de_tarefas` | Traz `equipe_avaliacoes_pendentes` | 200, campo presente (lista vazia: não há avaliação pendente de membro da equipe nos dados de teste) |

Depois do teste, os perfis e o gestor do departamento foram restaurados.

