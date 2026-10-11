# Evidências — Central de Pendências e Ausências (tarefas 11 a 13, 20, 21 e 24)

Telas construídas em 10/10/2026 no frontend Streamlit. O Figma não tinha a tela em que o gestor e o RH
decidem férias e correções de ponto: ela foi desenhada antes, na seção 19.

| Nó do Figma | O que é | Código |
|---|---|---|
| 436:1145 | Central de Pendências, aba Férias (Gestor, RH e Admin) — **novo, seção 19** | `frontend/pagina_central.py` |
| 436:1308 | Central de Pendências, aba Correções de ponto — **novo** | idem |
| 436:1473 | Modal "Decidir férias", com a conferência de conflitos — **novo** | idem |
| 436:1506 | Modal "Rejeitar correção de ponto" — **novo** | idem |
| 31:37 (F13) | "Minhas pendências": a Central do colaborador, com a trilha por assunto | idem |
| 243:846 | RH — Ausências | `frontend/pagina_ausencias.py` |
| 243:1127 e 243:1153 | Modais "Rejeitar ausência" e "Registrar ausência" | idem |

As regras de apresentação ficam em `frontend/decisoes_modelo.py` (sem Streamlit).

**Endpoints usados**
- filas: `central_de_tarefas` (`fila_ferias_pendentes`, e só a contagem de documentos e desligamentos) e
  `correcoes_ponto`, as duas já no escopo de quem pede (o Gestor não recebe documentos);
- férias: `ferias/{id}/verificar_conflito`, `ferias/{id}/aprovar` e `ferias/{id}/rejeitar`;
- correções: `correcoes_ponto/{id}/aprovar` e `correcoes_ponto/{id}/rejeitar` (com motivo);
- ausências: `ausencias?status=...`, `ausencias/{id}/aprovar`, `ausencias/{id}/rejeitar`, `ausencias/{id}/registrar`
  e `ausencias/{id}/comprovante`;
- "Minhas pendências": `minhas_solicitacoes`, `minhas_ferias`, `minhas_ausencias`, `minhas_pendencias_documento` e
  `minhas_correcoes_ponto`.

## Backend: duas falhas de escopo corrigidas

`correcoes_ponto` (GET) e `central_de_tarefas` calculavam o escopo do Gestor pelo departamento que ele gerencia.

- **A falha:** se o perfil era GESTOR mas a pessoa não gerenciava nenhum departamento, o código caía no ramo "RH e
  Admin veem tudo".
- **O efeito:** essa pessoa recebia as filas de todos os departamentos (férias, documentos, desligamentos e
  correções de ponto). Era vazamento de leitura; as decisões já conferiam o escopo e recusavam.
- **A correção:** o Gestor sem departamento passa a receber filas vazias.

A segunda falha estava em `central_de_tarefas`.

- **A falha:** a fila de documentos do Gestor trazia os registros inteiros dos documentos pendentes da equipe.
  Só RH e Admin decidem documentos, e o Figma (241:560) diz que o gestor nunca vê documentos pessoais.
- **A correção:** a fila de documentos do Gestor sai vazia.

Como foi publicado e conferido:
- `--dry-run` mostrou só os endpoints alterados (2, e depois 1), e cada `push` publicou só eles;
- o `pull` seguinte trouxe as mudanças;
- por HTTP, sem token e com token inválido, a resposta foi 401;
- `python tools/checar_endpoints.py`: 185 endpoints autenticados, nenhuma falha.

Não houve teste com contas reais de Gestor (com e sem departamento), porque o login pede um código enviado por e-mail.

## Como repetir

```
python tools/testar_decisoes.py   # 50 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 50 de 50.** Os outros testes do frontend continuam passando.

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Escopo (13) | O colaborador só vê "Minhas pendências": a tela não pede as filas | ok |
| Escopo (13) | O Gestor vê o que o backend devolve no escopo dele e não tem filtro de departamento | ok |
| Escopo (13) | RH filtra por departamento; Admin sem colaborador decide todos | ok |
| Próprio pedido | Ninguém recebe "Decidir", "Aprovar" ou "Rejeitar" no próprio pedido: férias, correção ou ausência | ok |
| Sucesso | "Decidir" mostra a conferência de conflitos e aprova ou rejeita as férias | ok |
| Sucesso | Correção: "Aprovar" direto; "Rejeitar" envia o motivo | ok |
| Sucesso | Ausência: aprovar, rejeitar com justificativa, registrar a aprovada e abrir o comprovante | ok |
| Restrito (21) | Gestor fora do departamento: a recusa do backend aparece como alerta, sem quebrar a tela | ok |
| Erro | Sem motivo (menos de 5 caracteres): mensagem no modal, sem chamar a API | ok |
| Erro | Recusa do backend no modal, que continua aberto (fora do escopo; CID na observação) | ok |
| Erro | Sem a conferência de conflitos, a decisão continua possível, porque a conferência só informa | ok |
| Erro | Erro ao carregar: a Central e Ausências mostram alerta; erro só nas correções deixa o resto da tela de pé | ok |
| Erro | Falha parcial em "Minhas pendências": aviso, e o que carregou aparece | ok |
| Vazio | Fila de férias vazia; aba de ausências vazia | ok |
| Permissão | Colaborador e Gestor que abrem Ausências pelo endereço veem "só do RH e do Admin", e a tela não carrega | ok |
| Carregando | Spinner enquanto as filas carregam, e "Conferindo conflitos..." no modal | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-central-decisoes/`](frontend-central-decisoes/):

| Print | Compare com |
|---|---|
| `1-central-ferias` | 436:1145 |
| `2-decidir-ferias` | 436:1473 |
| `3-central-correcoes` | 436:1308 |
| `4-rejeitar-correcao` | 436:1506 |
| `5-minhas-pendencias` | 31:37 (F13) |
| `6-ausencias` | 243:846 |
| `7-rejeitar-ausencia` | 243:1127 |
| `8-registrar-ausencia` | 243:1153 |
| `9` a `11` | tema escuro (`frontend/theme.py`, `_ESCURO_CSS`) |

## Decisões e diferenças em relação ao Figma

- **Decisão de férias e de correções desenhada antes.** A seção 4 do Figma dizia que as filas de decisão ficam na
  Central de Pendências, mas só existia a visão do colaborador (31:37). A seção 19 (436:1142) foi desenhada em
  10/10/2026 a partir da tela de Ausências (243:846).
- **Correção aprovada sem modal.** O horário pedido já está na linha. A recusa exige motivo, então tem modal.
- **"Minhas pendências" sem avaliações.** A seção "Avaliações e desenvolvimento" do F13 fica para quando a
  Trajetória existir. Decisões com mais de 30 dias saem da lista.
- **Documentos e desligamentos só como número.** A conferência de documentos tem tela própria (RH e Admin), e
  Desligamentos ainda não existe (tarefa 54).
- **Botão vermelho nos modais de recusa.** O "Recusar" da Conferência de documentos (244:1035) também ficou vermelho,
  como no Figma; antes era âmbar.
