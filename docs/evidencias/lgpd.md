# Evidências de LGPD

Registros de verificação das tarefas de adequação à LGPD. **Regras:** sem nome, CPF, e-mail, senha ou token; contas de teste só pelo papel; ids de registro são de dados de teste.

## Exercício de incidente: token de acesso vazado

**Identificador:** `EX-2026-001` (simulação, não é incidente real). **Data:** 08/10/2026. **Plano seguido:** [plano-de-incidentes.md](../lgpd/plano-de-incidentes.md). **Conta usada:** conta de teste de perfil Colaborador (usuário 15).

### Cenário

O token de uma sessão da conta de teste vazou. Uma segunda sessão, a do titular legítimo, continua em uso.

### Percurso pelo plano

| Etapa do plano | O que foi feito | Resultado |
|---|---|---|
| **Situação** | O "atacante" usou o token vazado | `auth/me` e `meu_perfil_colaborador` responderam 200 (sessão 46) |
| **Detecção** (seção 2) | O Admin consultou `GET auditoria` filtrando pela conta | 18 eventos `login_sucesso`; os dois últimos com **10 segundos de diferença**, o sinal de dois acessos quase simultâneos |
| **Avaliação** (seção 3) | Classificação do risco | **Baixo**: conta de teste, dados fictícios, nenhum dado sensível, financeiro ou de menor, uma pessoa. Sem comunicação à ANPD; decisão registrada |
| **Contenção** (seção 4) | O titular revogou a sessão suspeita com o próprio token | `auth/sessoes/46/encerrar` → 200 |
| **Verificação** | O token vazado foi usado de novo | `auth/me` → 401 "Sessao encerrada ou expirada."; `meu_perfil_colaborador` → 401 |
| | O token do titular | Continuou válido (200) |
| **Registro** (seção 6) | Evento na auditoria | 1 evento `encerrar_sessao` para a sessão 46 |

### Registro interno (modelo da seção 6)

| Campo | Conteúdo |
|---|---|
| Identificador | EX-2026-001 |
| Datas | Ocorrência, descoberta, contenção e encerramento: 08/10/2026 (exercício) |
| Quem detectou e como | Administrador, pela consulta à auditoria |
| Descrição | Token de sessão da conta de teste usado em paralelo à sessão do titular |
| Dados e titulares afetados | Nenhum dado real; uma conta de teste |
| Nível de risco | Baixo (simulação) |
| Contenção | Revogação da sessão pelo titular; efeito imediato nos endpoints |
| Comunicação | ANPD: não (sem risco real). Titulares: não |
| Causa e prevenção | Simulada. Em incidente real: investigar como o token vazou e trocar a senha da conta |

### O que o exercício mostrou

1. **A contenção funciona e é imediata**, porque todo endpoint autenticado confere a sessão do token. Esse era justamente o ponto fraco antes da guarda de acesso: o token valia por 1 hora mesmo depois do logout.
2. **A consulta à auditoria exige token válido de RH ou Admin** (vale 1 hora). Em uma resposta real, a pessoa que investiga precisa estar logada.
3. **A auditoria devolve os eventos mais recentes primeiro**, sem paginação; numa investigação longa, use os filtros de usuário e ação.

### Verificação

Este arquivo não contém e-mail, token, CPF nem nome real.

## 4.14 Mínimo de pessoas nos indicadores

| Cenário | Esperado | Obtido |
|---|---|---|
| `GET indicadores` com 13 ativos, um departamento com 10 e dois grupos pequenos (departamento e sem departamento) | Só o departamento com 10 aparece; `minimo_pessoas = 5`, `grupos_omitidos = 2` | Igual; os totais seguem visíveis, porque há mais de um grupo omitido |
| `GET indicadores/exportar_csv` | Mesmo corte e as linhas `minimo_pessoas_por_grupo` e `grupos_omitidos` | Igual |

Caso de um único grupo omitido, com a variável `INDICADORES_MINIMO_PESSOAS` temporariamente em 2 (11 pessoas em um departamento, 2 em outro e 1 em um terceiro): `grupos_omitidos = 1`, `totais_omitidos = true`, `headcount` nulo e, no CSV, `headcount_ativos,omitido` e `headcount_total,omitido`. Com o mínimo em 3 havia 2 grupos omitidos e os totais seguiam visíveis. As variáveis de teste são temporárias e devem ser apagadas do Xano.

## 4.16 Exportação dos dados do titular

| Cenário | Esperado | Obtido |
|---|---|---|
| `GET meus_dados` (json) | Todas as categorias, sem senha nem código de acesso | 200; usuário, colaborador, histórico, documentos, férias, ausências, ponto, banco de horas, avaliações, metas, PDI, solicitações, notificações e sessões; nenhum campo de senha, `otp_` ou `reset_senha` |
| `GET meus_dados?formato=csv` | Resumo por registro | 200; cabeçalho `categoria,id,tipo,status,data` |
| `GET meus_dados?formato=xml` | Recusa | 400 |
| Auditoria | Um evento `exportar_meus_dados` por exportação, com o formato | 2 eventos (json e csv) |

A rota só devolve os dados de quem está autenticado: não recebe id de colaborador.

## 3.49 Resultado da pesquisa de clima

| Cenário | Esperado | Obtido |
|---|---|---|
| `GET pesquisas_clima/{id}/resultados` com a pesquisa aberta | Recusa | 400 |
| Mesma consulta depois de encerrar, com 1 resposta e mínimo de 2 | 200 sem nenhum grupo nem total | 200 e lista vazia |

**Não verificado:** a supressão complementar com respostas suficientes para o total aparecer (precisa de pelo menos 3 respondentes em departamentos diferentes, e só há uma conta de teste disponível).

## 4.27 Upload de arquivo privado

| Cenário | Obtido |
|---|---|
| `POST documentos` multipart com `imagem_frente` (campo `image`) | 400 "Missing param: path" |
| O mesmo com o campo declarado como `file` | 403 "Not supported. Please upgrade your Xano instance." |
| O mesmo `POST documentos` só com `arquivo_url` aprovado | 200 |

O upload de arquivo privado não é suportado no plano atual do Xano.

## 4.17 Pedido LGPD

| Cenário | Esperado | Obtido |
|---|---|---|
| Pedido `privacidade_lgpd` sem subtipo | Recusa | 400 |
| Subtipo desconhecido | Recusa | 400 |
| Subtipo em solicitação de outro tipo | Recusa | 400 |
| Pedido com subtipo `correcao` | Aceito, com prazo de abertura + 15 dias | 200; `prazo_resposta` = abertura + 15 dias (UTC) |
| Fila do RH (`solicitacoes`) | Mostra o pedido com o prazo | Sim |
| RH atende o pedido | Aceito, com notificação ao colaborador | 200; notificação `solicitacao_respondida` recebida; auditoria com a justificativa |

**Não verificado:** o alerta de prazo próximo (3 dias ou menos) na `central_de_tarefas`. O campo `pedidos_lgpd_prazo_proximo` está na resposta e veio vazio, porque um pedido recém-criado vence em 15 dias e não há como antecipar a data.

## 4.18 Preferências de privacidade

| Cenário | Esperado | Obtido |
|---|---|---|
| Preferência padrão de um adulto | Nada oculto, `padrao = true` | Igual |
| Colaborador sai do mural | Outro usuário não vê o reconhecimento; o próprio colaborador vê no mural e em "recebidos"; Admin vê | Igual |
| Menor de 18 anos sem linha gravada | Fora de aniversariantes e mural para os demais | Igual (ver 4.23) |

**Não verificado:** o colaborador sair da lista de aniversariantes e continuar se vendo nela. Os dados de teste não permitem mudar a data de nascimento do colaborador usado (o CPF cadastrado não passa na validação). A ocultação em aniversariantes foi observada com o menor.

## 4.21 Limpeza de retenção na rotina diária

Com `EMAIL_RETENCAO_DIAS` e `SESSAO_RETENCAO_DIAS` temporariamente em 0:

| Cenário | Esperado | Obtido |
|---|---|---|
| `status_operacional` antes | `emails_enviados_limpos = 10` | 10 |
| Primeira execução | Aplica a mesma contagem | 10 |
| Segunda execução | Zerada | 0 |
| Limpeza de sessões | Sem IP nem dispositivo para limpar | 0: o login não grava esses campos, então estão sempre vazios |

**Não verificado:** a lista de desligados com prazo de guarda cumprido, porque os dois desligados de teste já haviam sido anonimizados.

## 4.22 Anonimização

| Cenário | Esperado | Obtido |
|---|---|---|
| Colaborador ativo | Recusa | 400 |
| O próprio cadastro | Recusa | 403 |
| Justificativa com menos de 5 caracteres | Recusa | 400 |
| Perfil sem permissão (Colaborador) | Recusa | 403 |
| Colaborador desligado, sem documentos em guarda | Anonimiza | 200 |
| Nova tentativa no mesmo colaborador | Recusa | 400 |
| Depois da anonimização | Nome, e-mail, telefone, nascimento e dados bancários trocados por marcadores; usuário desativado e renomeado; nenhum registro excluído; indicadores iguais; auditoria sem valores | Igual |

**Não verificado:** a recusa por documento com prazo de guarda vigente, porque o sistema não permite cadastrar documento para colaborador já desligado, então não há como montar o caso com os dados de teste. A regra está no código (`retencao_ate` no futuro).

## 4.23 Menor de 18 anos

| Cenário | Esperado | Obtido |
|---|---|---|
| Pré-cadastro de aprendiz de 16 anos | Aceito | 200 |
| Criar o acesso sem documento de responsável legal | Recusa | 400 |
| Criar o acesso com o documento ainda pendente | Recusa | 500 na primeira rodada (defeito corrigido: o endpoint não lia a data de nascimento); repetido depois da correção: 400 |
| Criar o acesso com o documento aprovado | Aceito | 200 |
| Aniversariantes (aniversário em outubro) | O menor não aparece | Não aparece |
| Mural para outro usuário | O menor não aparece; RH/Admin veem | Igual |

A "ativação do contrato" foi interpretada como a criação do acesso (`usuarios POST`): o documento precisa de um colaborador para ser anexado, então o pré-cadastro não pode ser bloqueado.

