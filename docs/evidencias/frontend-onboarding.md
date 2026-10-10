# Evidências — Onboarding do primeiro acesso (tarefa 68)

Onboarding refeito sobre o desenho de 10/10/2026 (fluxo F37 "Onboarding e pendências do primeiro acesso" e
Etapa 3 do F01), no frontend Streamlit da branch `feature/frontend-login-f01`.

| Nó do Figma | Tela | Código |
|---|---|---|
| 310:2477 | Onboarding, boas-vindas depois da troca da senha temporária | `frontend/pagina_onboarding.py` |
| 309:1048 | Meu onboarding (as 13 etapas por responsável) | `frontend/pagina_meu_onboarding.py` |
| 309:1446 | Início com o card do onboarding em andamento | `frontend/pagina_inicio.py` |
| 309:1249 | Documentos pendentes | **não construída**: depende da tela Documentos (tarefas 26 a 28) |

As regras de apresentação ficam em `frontend/onboarding_modelo.py` (sem Streamlit) e as consultas, em
`frontend/onboarding_dados.py` (`colaboradores/{id}/onboarding`, `onboarding_item/{id}/concluir`,
`minhas_pendencias_documento`, `meu_perfil_colaborador` e `organograma`).

## Como repetir

```
python tools/testar_onboarding.py    # 45 verificações
python tools/testar_login_f01.py     # 51 verificações (inclui o caminho de primeiro acesso até o Início)
```

Os dois rodam sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 45 de 45 e 51 de 51.**

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | 13 etapas contadas por responsável: 2 do colaborador, 7 do RH, 4 do gestor (igual a `onboarding_POST`) | ok |
| Sucesso | Boas-vindas: as 6 linhas e os detalhes do Figma com 3 de 13 ("Com o RH · 2 de 6 concluídas"…) | ok |
| Sucesso | "Meu onboarding": colunas "Com você", "Com o RH" e "Com seu gestor", com as etapas juntadas como no Figma | ok |
| Sucesso | "previsto para" = início + 30, 60 e 90 dias (01/10/2026 → 31/10, 30/11 e 30/12/2026) | ok |
| Sucesso | "Concluída em dd/mm/aaaa" a partir do `concluido_em` do backend | ok |
| Sucesso | Documentos: "2 de 4 enviados · faltam CTPS e certificado de reservista" (pedido cancelado não conta) | ok |
| Sucesso | Card do Início com o progresso, a próxima pendência e o prazo mais próximo | ok |
| Vazio | Conta sem colaborador e colaborador sem checklist: sem card e "Você não tem um onboarding em andamento" | ok |
| Vazio | Onboarding concluído ou as 13 etapas feitas: o card do Início some | ok |
| Erro | O onboarding não carrega: alerta no cartão, sem exceção; o Início continua sem o card | ok |
| Carregando | Spinner dentro do cartão ou da página | verificado no navegador |

O backend responde 403 a quem não pode ver o onboarding: a tela mostra esse erro como os demais, no cartão. Não
há estado "bloqueado" próprio nesta tela.

## Verificado no navegador (Chrome, API simulada)

Prints só do app (dados fictícios), em [`frontend-f01/`](frontend-f01/): `6-onboarding`, `7-meu-onboarding` e
`8-inicio-com-onboarding`. Os prints do Figma não foram versionados porque as telas de exemplo ainda usam uma
pessoa com e-mail pessoal (tarefa 60); compare abrindo os nós acima.

- A boas-vindas mostra as 6 linhas, "3 de 13", o resumo "Gestor · Departamento · CLT · 44h/semana", o botão
  "Enviar documentos" e a nota "São 13 etapas: 2 suas, 7 do RH e 4 do seu gestor…".
- "Ver todas as etapas" abre "Meu onboarding"; nela, o item ativo do menu continua sendo "Início", como no Figma, e
  "← Voltar ao Início" volta.
- O card do Início fica acima dos indicadores e "Continuar onboarding →" abre "Meu onboarding".

## Decisões e diferenças em relação ao Figma

- **Saudação neutra:** "Bem-vindo(a), Nome!". O exemplo do Figma ("Bem-vinda, Juliana!") é de uma pessoa; o
  cadastro não guarda gênero.
- **"Enviar documentos"** ainda não abre a tela Documentos (tarefas 26 a 28): na boas-vindas leva ao Início com
  o aviso "A tela Documentos ainda está em construção. Os documentos pedidos aparecem no Início."; em "Meu
  onboarding" mostra o mesmo aviso. A tela "Documentos pendentes" (309:1249) fica para depois da tela Documentos.
- **Card do Início:** entra no topo do Início existente (62:38), acima dos indicadores, em vez de substituir a
  página. O desenho 309:1446 mostra só o card e as pendências; manter o resto do Início é a escolha que não tira
  informação de ninguém e pode ser revista.
- **"Ver todas as etapas"** é um link abaixo da nota na boas-vindas: o fluxo F37 tem essa passagem, mas a tela do
  Figma não desenha o controle.
- **Nota de rodapé de "Meu onboarding"** ("As 13 etapas vêm do backend…") é anotação de projeto no Figma e não
  aparece no app.
- **Cache de 20 segundos** dos dados do onboarding em `st.session_state`, para o Início não repetir as consultas a
  cada interação (limite do plano do Xano: 10 requisições a cada 20 segundos). Ele é apagado no fim da sessão.
