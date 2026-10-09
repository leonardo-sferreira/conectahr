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

