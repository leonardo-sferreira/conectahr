# Evidências de segurança — Parte 1

Resultado das verificações da Parte 1 da change `corrigir-brechas-e-alinhar-documentacao`, hoje na change `concluir-mvp-conectarh` (seção 3). Todos os testes foram feitos por HTTP contra o workspace Xano do projeto, entre 06/10/2026 e 08/10/2026.

**Regras deste arquivo:** sem e-mail, CPF, senha ou token. As contas aparecem pelo papel: *Admin* (conta de administração do projeto), *conta de teste A* (perfil Colaborador, depois trocado temporariamente para RH e Gestor), *conta de teste B* e *conta de teste C* (criadas para os testes, a B desativada). Os ids de registro são de dados de teste.

**Limite do plano do Xano:** 10 requisições por 20 segundos (HTTP 429). Os testes automatizados esperam entre as chamadas.

## 1.1 Spike da sessão no token

| Cenário | Requisição | Esperado | Obtido |
|---|---|---|---|
| Dois logins da mesma conta devolvem sessões diferentes | `GET auth/me` com cada token | `sessao_id` de cada token | Sessões 30 e 31, ambas ativas no banco (`xano workspace pull --records`) |

## 1.4 Sessão no token

| Cenário | Requisição | Esperado | Obtido |
|---|---|---|---|
| Logout encerra só a sessão do token | `POST auth/logout` com o token A | A recusado, B aceito | A: 401 "Sessao encerrada ou expirada."; B: 200 |
| `encerrar_outras` preserva a sessão do token | `POST auth/sessoes/encerrar_outras` com D | D aceito, E recusado | D: 200; E: 401 |
| Encerrar sessão de outro usuário | `POST auth/sessoes/{id do Admin}/encerrar` com a conta de teste A | Negado; sessão do Admin intacta | 403 "Voce so pode encerrar as proprias sessoes."; Admin segue 200 |
| Encerrar a própria sessão | `POST auth/sessoes/{id}/encerrar` com D | D passa a ser recusado | 200; depois 401 |

## 1.5 a 1.8 Guarda de acesso

`python tools/checar_endpoints.py`: **173 endpoints autenticados, 0 falhas, 0 grupos com problema de swagger.**

| Cenário | Requisição | Esperado | Obtido |
|---|---|---|---|
| Senha temporária só usa as rotas de primeiro acesso | `auth/me`, `auth/minhas_sessoes`, `auth/sessoes/encerrar_outras`, `auth/senha` (PATCH) | 200 | 200 em todas |
| Senha temporária nas demais rotas | `usuarios`, `minhas_delegacoes`, `status_operacional`, `auditoria`, `indicadores`, `instrumentos_normativos/{id}/aprovar`, `metas`, `pdi`, `perguntas_clima/{id}/responder`, `central_de_tarefas`, `meu_perfil_colaborador` | 401 "Troque a senha temporaria antes de continuar." | 401 em todas (para `metas` e `pdi` o corpo precisa ter todos os campos; com campos faltando o Xano devolve 400 antes da guarda) |
| Depois da troca de senha | `GET minhas_delegacoes` | 200 | 200 |
| Conta desativada, token emitido antes | `auth/me`, `minhas_delegacoes`, `auth/minhas_sessoes`, `ponto/marcar`, `ferias/solicitacoes` | 401 "Usuario inativo.", sem gravar nada | 401 em todas; o login da conta também foi recusado (403) |
| Admin não perde acesso | 28 + 14 leituras sem parâmetro obrigatório | 200 | 42 de 43 em 200; a exceção é `minhas_solicitacoes_desligamento`, 403 por regra (só colaborador ou gestor) |
| Guarda por perfil | 10 leituras do grupo Colaboradores | Nenhum 401 | RH: 10 em 200. Gestor e Colaborador: 4 em 200 e 6 em 403 (rotas de outro perfil) |

## 1.9 Revogação em massa

| Cenário | Requisição | Esperado | Obtido |
|---|---|---|---|
| Desativar conta com duas sessões ativas | `PATCH usuarios/{id}/status` com `ativo: false` pelo Admin | Os dois tokens recusados | Sessões 40 e 41 → 401 "Sessao encerrada ou expirada." (revogadas, não só "inativo") |
| Reativar a conta | `PATCH usuarios/{id}/status` com `ativo: true` | Sessões antigas seguem revogadas; login novo funciona | Token antigo 401; novo login 200 (sessão 42) |
| Desligamento (`aprovar` imediato e `concluir`) | — | Mesma revogação, dentro da transação | **Não exercitado ao vivo:** desligaria um colaborador de forma irreversível. O bloco de código é o mesmo. |

## 1.10 Reenvio do código de acesso

| Cenário | Esperado | Obtido |
|---|---|---|
| Reenvio logo após o login (< 60 s) | Recusado, sem e-mail | 429 "Aguarde um minuto..." |
| 5 códigos errados | Recusados | 403 nas 5 tentativas |
| 6ª tentativa | 403, não 429 (o código foi descartado) | 403 |
| Reenvio depois de 5 erros | Recusado | 403 |
| Novo login, 3 reenvios com 61 s de intervalo, 4º reenvio | 200, 200, 200 e 429 | 200, 200, 200 e 429 |
| Só um novo login gera código válido | Token emitido | 200 com token |

## 1.11 Bloqueio de autoaprovação

| Cenário | Esperado | Obtido |
|---|---|---|
| Admin aprova ou rejeita as próprias férias, aprova a própria ausência e o próprio documento | 403, status inalterado, evento na auditoria | 403 nos 4; status inalterados; 4 eventos `autoaprovacao_bloqueada` (falha) em `auditoria GET` |
| Gestor (conta de teste A com perfil Gestor) aprova a própria correção de ponto | 403 e evento | 403 "Voce nao pode decidir uma solicitacao propria."; 1 evento para `correcao_ponto` |
| Admin aprova a correção de outra pessoa | 200, sem regressão | 200 "Correcao de ponto aprovada com sucesso." |

## 1.12 e 1.13 Anonimato da pesquisa de clima

| Cenário | Esperado | Obtido |
|---|---|---|
| Resposta válida (nota 4) | 200; agregado +1; nenhuma linha individual nova | 200; agregado (pergunta 1, dept. 4, nota 4) = 1; `resposta_clima` segue com 2 linhas antigas |
| Resposta repetida | Recusada | 400 "Voce ja respondeu esta pergunta." |
| Nota 6 | Recusada | 400 "A nota deve estar entre 1 e 5." |
| Pesquisa com período encerrado | Recusada, sem participação | 400 "Esta pesquisa esta fora do periodo de respostas."; 0 participações gravadas |
| Resultados | Soma do agregado; grupo abaixo do mínimo suprimido | Pergunta 1: quantidade 3, média 4 (por departamento e geral); pergunta 2 (abaixo do mínimo de 2) não aparece |
| Consolidação das respostas antigas, 1ª execução | Agregado igual ao legado | 2 linhas consolidadas; soma dos agregados = 2, nota por nota |
| Consolidação, 2ª execução | Nada muda | `ja_executada_antes: true`, 0 linhas; 1 evento na auditoria |

**Não exercitado:** pesquisa inativa (não há como encerrar uma pesquisa antes da tarefa `pesquisas_clima/{id}/encerrar`), colaborador desligado (a conta é desativada no desligamento e a guarda barra antes) e supressão de um grupo que tem respostas, mas menos que o mínimo (sem dados). **Limitação aberta:** os resultados ainda permitem deduzir uma resposta por complemento ou por diferença (tarefa 3.49 de `concluir-mvp-conectarh`).

## 1.14 Troca de e-mail de conta

| Cenário | Esperado | Obtido |
|---|---|---|
| Admin troca o e-mail da conta de teste B | Alerta no `email_outbox` para o e-mail anterior; auditoria com os dois valores | 1 linha no outbox, destinatário = e-mail anterior, status `pendente`, assunto "O e-mail de acesso da sua conta foi alterado", **sem** o endereço novo no texto; evento `atualizar_usuario` com valor anterior e novo |

## 1.15 Swagger

| Cenário | Esperado | Obtido |
|---|---|---|
| Antes: grupos com token | Documentação protegida | 7 grupos abriam o `apispec` com o token (200); sem token, 403 |
| Antes: grupos sem o campo | Fechada | **Aberta para qualquer pessoa**: 200 sem token e com qualquer token (3 grupos) |
| Depois: `swagger = {active: false}` nos 10 grupos | `apispec` indisponível | 404 em todos os 10, com ou sem token |
| Tokens antigos do histórico do git | Sem validade | Nenhum dos 7 tokens do histórico continua no servidor (trocados por valores novos, guardados só no Xano) |

O repositório é **público**: os tokens antigos continuam no histórico do git, mas não valem mais. O `tools/checar_endpoints.py` reprova grupo com swagger ligado, sem a configuração ou com token no arquivo.
