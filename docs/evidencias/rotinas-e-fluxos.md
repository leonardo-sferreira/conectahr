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
