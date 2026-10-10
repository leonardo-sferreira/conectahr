# Design

Esta change não toma decisão de produto nova. O desenho das telas, o mapa de nós do Figma e a lista das telas
que faltavam estão em:

- `openspec/changes/archive/2026-10-09-concluir-mvp-conectarh/design.md`, decisões C2 e C3;
- `openspec/changes/archive/2026-10-08-implementar-frontend-streamlit/design.md`, que traz a decisão
  "Protótipo Figma como fonte única" e a tabela de telas que faltam (levantamento de 08/10, hoje
  **desatualizado**: veja a seção abaixo);
- `frontend/AGENTS.md`, com as regras de tela, como rodar e o padrão do `api_client.py`;
- `docs/deploy.md`, para a publicação e o plano de rollback.

## Levantamento do Figma em 09/10/2026

Arquivo `fph1M5tB4rA4gqfIysSmkn`. O levantamento de 08/10 listava 20 telas como "A desenhar". Em 09/10 o
Figma foi conferido de novo (nomes de frames e textos) e comparado com a spec principal e com `docs/lgpd/`.

### O que já existia

A página "Fluxos — apresentação" tem os fluxos F01 a F39 (veja a revalidação de 10/10/2026) e a página "ConectaRH — Protótipo" tem as seções 1 a 12.
Não faltavam: Sessão expirada, Organograma, Calendário, Comunicados e FAQ, Pesquisa de clima, Configurações
(Segurança, Notificações, Privacidade), Pedir desligamento, Delegações, Minha equipe, Indicadores, Usuários e
perfis, Sessões ativas, Estrutura da empresa (departamentos, cargos e feriados) e Colaboradores.

| Tela | Nó | Fluxo |
|---|---|---|
| Login — Sessão expirada | 224:619 | F01 |
| Configurações — Segurança | 224:1293 | F03 |
| Configurações — Notificações | 224:2027 | F04 |
| Configurações — Privacidade | 224:2176 | F04 |
| Perfil | 224:2459 | F05 |
| Organograma | 224:3593 | F05 |
| Pedir desligamento | 224:4056 | F05 |
| Calendário | 233:2394 | F07 |
| Comunicados e FAQ | 225:4310 | F11 |
| Pesquisa de clima | 225:4668 | F12 |
| Central de Pendências (gestor) | 225:5122 | F13 |
| Gestor — Minha equipe | 248:409 | F14 |
| Gestor — Delegações | 248:2235 | F17 |
| Gestor — Indicadores da equipe | 248:2694 | F18 |
| RH — Solicitações ao RH | 225:5299 | F19 |
| RH — Colaboradores | 249:466 | F21 |
| RH — Desligamentos | 249:3075 | F24 |
| RH — Pedidos LGPD | 249:5709 | F28 |
| Auditoria e Regras | 225:6784 e 225:6895 | F29 |
| Admin — Usuários e perfis | 249:6059 | F30 |
| Admin — Sessões ativas | 249:6819 | F31 |
| Admin — Estrutura da empresa | 249:6993 | F32 |
| Admin — Indicadores gerais | 249:7492 | F33 |

### O que faltava e foi desenhado em 09/10/2026

A spec ou `docs/lgpd/` exigem as telas abaixo e o Figma não as tinha. Cada uma foi desenhada em modo claro
(página "ConectaRH — Protótipo", seções 13 a 16) e em modo escuro (página "Protótipo — Dark", mesmas seções com
o sufixo " — Dark"), com os modais e os estados que a spec descreve.

| Seção (claro / escuro) | Tela | Nó (claro) | Requisito |
|---|---|---|---|
| 13 (282:866 / 292:974) | Login — Passo 1, com link do aviso | 282:868 | Transparência: aviso acessível antes do login |
| 13 | Aviso de privacidade (sem login) | 285:874 | Transparência: 7 conteúdos do aviso |
| 13 | Aviso de privacidade (logado) | 285:1073 | Transparência |
| 13 | Configurações — Privacidade, com contato do encarregado | 286:878 | Transparência: contato do encarregado |
| 13 | Modal Baixar meus dados (JSON/CSV) e arquivo gerado | 286:1062 e 286:1092 | Acesso e portabilidade dos próprios dados |
| 14 (287:882 / 292:1584) | RH — Regras: criar, aprovar, simular e aplicar | 287:884 | Instrumentos e overrides; Aprovação, simulação e aplicação versionada |
| 14 | RH — Simulação de impacto | 288:886 | Simulação antes da publicação |
| 14 | Modais: Novo instrumento, Nova regra de override, Aprovar, Aprovar (autoaprovação bloqueada), Rejeitar, Aplicar, Aplicar (conflito bloqueia) | 288:1186, 288:1234, 288:1293, 288:1321, 288:1343, 288:1367, 288:1391 | Autoaprovação, Mediador/MTE, conflito não resolvido |
| 15 (289:898 / 292:2190) | RH — Rotina diária (antes) e (resultado), e Admin — Rotina diária | 289:900, 289:1190 e 289:1477 | Transições de status por rotina acionada manualmente |
| 15 | RH — Retenção e anonimização | 290:902 | Retenção e anonimização; revisão de retenção vencida |
| 15 | Modais: Executar rotina, Anonimizar, Anonimizar (recusado) | 290:1164, 290:1187, 290:1213 | Retenção e anonimização |
| 16 (291:906 / 292:2864) | Reconhecimentos: Mural, Recebidos (com feedback privado) e Mural vazio | 291:908, 291:1075, 291:1239 | Desenvolvimento e reconhecimento |
| 16 | RH — Moderar reconhecimentos | 291:1374 | Reconhecimento moderado |
| 16 | Modais: Reconhecer colega, Reconhecer colega (erro), Moderar | 291:1631, 291:1667, 291:1703 | Reconhecimento; visibilidade automática |

Também foram atualizados no Figma:

- **Menus por perfil (seção 7):** `Sidebar/RH` e `Sidebar/Admin` ganharam o grupo completo e os itens
  "Rotina diária" e "Retenção e anonimização"; a tabela de permissões ganhou as linhas Rotina diária, Retenção e
  anonimização, Reconhecimentos e Aviso de privacidade, e a linha Regras passou a citar simulação e aplicação.
- **Design System (página "Design System"):** o quadro novo "Design System — Modo escuro e componentes"
  (294:622) documenta os tokens do modo escuro, botões, campos, alertas, seleção, badges, modal, estados de
  decisão e as medidas de contraste. O subtítulo da página dizia "handoff em Reflex" e passou a dizer Streamlit.

### Decisões de desenho

- **Novos itens de menu, só para RH e Admin:** "Rotina diária" e "Retenção e anonimização" ficam no grupo RH
  (e no grupo ADMIN para o Admin). As demais telas existentes ainda mostram o menu antigo; o item aparece
  quando a tela for construída no Streamlit (o filtro de páginas por perfil é da tarefa 8).
- **Reconhecimentos:** o mural é aberto por Trajetória (aba), não por item novo de menu; a moderação do RH
  também (a tabela de permissões já dizia "Modera reconhecimentos" em Trajetória).
- **Texto do aviso:** igual a `docs/lgpd/aviso-de-privacidade.md`. Uma diferença: o documento diz "enquanto
  a tela não estiver disponível, envie o pedido ao encarregado". No Figma, o "Como exercer" já aponta para
  Configurações → Privacidade e mantém o encarregado como alternativa para quem ainda não tem acesso. Quando a
  tela for construída, o documento deve ser atualizado para o mesmo texto (tarefa 59).
- **Desligados no exemplo de Retenção:** as datas de guarda seguem `DESLIGADO_RETENCAO_DIAS` = 1825 (5 anos).

### Pendências que o levantamento encontrou e não resolveu

- **Estados de anexo (enviado, em verificação, liberado, bloqueado) em Documentos:** a spec "Quarentena e
  retenção de documentos" os descreve e o Design System tem o estado "Bloqueado" com esse exemplo, mas a tela
  Documentos não os mostra. Como o plano do Xano não aceita upload e o documento entra só por link, a decisão
  é do time; fica na tarefa 62.
- **Contraste:** o Design System dizia que todas as combinações passam em WCAG AA. A medição em 09/10 mostra
  texto de badge abaixo de 4,5:1 (verde sobre verde claro 3,0:1; âmbar-escuro sobre âmbar claro 2,6:1; vermelho
  sobre vermelho claro 4,2:1; cinza auxiliar `#737A85` sobre branco 4,3:1). O status sempre vem com texto, então
  a cor não é a única pista, mas o contraste precisa ser corrigido antes de declarar AA (tarefa 61).
- **E-mail de pessoa real no protótipo:** `docs/lgpd/operadores.md` manda trocar os exemplos do Figma por dados
  fictícios. Em Admin — Integrações e e-mails ainda aparece um e-mail pessoal (`j***@gmail.com`) e, no Passo 2 do login, um e-mail
  institucional de estudante (`l***@aluno.impacta.edu.br`); a revalidação de 10/10 achou os dois em todas as páginas
  (tarefa 60).
- **Telas existentes sem versão escura:** a página "Protótipo — Dark" tinha as 13 telas originais. Em 09/10 só
  as seções 13 a 16 ganharam versão escura; **atualizado em 10/10:** agora também existem as versões escuras das
  seções 5, 9, 10, 11, 12 e 17 (mesmos textos das claras, conferido). Continuam só em modo claro as seções 1 a 4
  e 6 a 8 e a página "Fluxos — apresentação" (tarefa 63).

## Revalidação de 10/10/2026

Revalidação do repositório e do Figma depois de telas novas. O que passou: `checar_endpoints` (184 endpoints, 0
falhas), `smoke_frontend`, `testar_login_f01` (48 de 48), sintaxe do Python, busca de segredos, `openspec validate
--all`, 87 links de `.md` sem quebra, e o aviso de privacidade do Figma idêntico a `docs/lgpd/aviso-de-privacidade.md`
(54 células e os 7 direitos). Dos 93 nós citados no repositório, 92 existem.

### O que mudou no Figma (feito por outra pessoa ou sessão)

| Item | Nó |
|---|---|
| Seção 17 "Onboarding — primeiro acesso e pendências" (claro) | 309:1046 |
| Seção 17 em modo escuro | 313:900 |
| Onboarding — meu checklist | 309:1048 |
| Onboarding — Documentos pendentes | 309:1249 |
| Início — onboarding em andamento (card de progresso e pendências) | 309:1446 |
| Modal/Enviar documento (CTPS) | 309:1591 |
| **Onboarding do F01, redesenhado** (substitui o 224:424, que não existe mais) | 310:2477 |
| Fluxo F37 "Onboarding e pendências do primeiro acesso" | 310:746 |
| Versões escuras das seções 5, 9, 10, 11 e 12 | 315:2699, 315:3253, 315:4158, 315:5724, 315:6608 |
| Design System — Senha, onboarding e menu | 314:786 |

### Onboarding: o desenho novo e o que a tela do Streamlit faz hoje

O desenho novo agrupa as 13 etapas do backend por responsável (2 do colaborador, 7 do RH, 4 do gestor, conferido
contando os `responsavel` de `onboarding_POST`). No F01 são 6 linhas (trocar a senha; enviar documentos; "Conferir
dados, acesso, contrato e jornada" com o RH; "Aprovar os documentos enviados"; "Definir metas iniciais" com o
gestor; "Acompanhamentos de 30, 60 e 90 dias"), o botão é **"Enviar documentos"** (leva a Documentos) e a nota
diz "São 13 etapas: 2 suas, 7 do RH e 4 do seu gestor…". "Meu onboarding" mostra as 13 em três colunas.

`frontend/pagina_onboarding.py` foi feita sobre o nó antigo 224:424: lista as 13 em linha única, o botão é
"Continuar etapa atual" (leva ao Início) e a nota diz que os acompanhamentos serão "agendados automaticamente
pelo RH", o que o plano do Xano não faz (sem tarefas agendadas). Por isso a tarefa 17 voltou a ficar aberta.

Dados que o desenho novo pede e o backend já tem ou não tem:

- "Concluída em 01/10/2026": `onboarding_item.concluido_em` existe.
- "2 de 6 enviados · faltam CTPS…" e "Prazo: 10/10/2026": `minhas_pendencias_documento` traz `prazo`; a contagem
  "enviados de obrigatórios" precisa ser calculada com `documentos_obrigatorios` e `meus_documentos`.
- "previsto para 31/10/2026" nos acompanhamentos: **não há campo**. Só dá para calcular `onboarding.data_inicio` +
  30, 60 e 90 dias, e isso é uma regra nova para registrar.
- O botão "Enviar documentos" e a tela "Documentos pendentes" dependiam da tela Documentos (tarefas 26 a 28), que
  foi construída em 10/10/2026 (ver "Privacidade e Documentos"); o upload só entra por link (decisão registrada em
  `docs/regras-de-negocio.md`).
- A saudação do desenho é "Bem-vinda, Juliana!": é de uma pessoa de exemplo. A tela deve usar texto neutro
  ("Bem-vindo(a)"), porque o cadastro não guarda gênero.

### Divergências abertas (cada uma virou tarefa; as três primeiras foram resolvidas em 10/10/2026)

- **Numeração dos fluxos repetida.** Existem dois "F37": "RH — Regras: criar, aprovar, simular e aplicar" (09/10)
  e "Onboarding e pendências do primeiro acesso" (10/10). Além disso, no aviso de privacidade os códigos F01 a F19
  são as *finalidades* da LGPD (`docs/lgpd/registro-de-operacoes.md`), outro conjunto de códigos que se confunde com
  os fluxos F01 a F39. Proposta: manter o Onboarding como F37 (liga ao F01, e a numeração do índice já o coloca na
  coluna "Acesso e conta") e renumerar o fluxo de Regras para F40; deixar as finalidades como "Finalidade 1…19" no
  aviso. A decisão é do time (tarefa 69).
- **Spec x aviso x backend (IP e dispositivo).** A spec "Transparência sobre o tratamento de dados" exige que o
  aviso informe que IP e dispositivo "são registrados no login e na auditoria". O aviso e o backend dizem o
  contrário: hoje o login não grava `endereco_ip` nem `dispositivo`. Ou a spec muda para "poderão ser registrados" ou
  o backend passa a gravar; enquanto isso o aviso diz a verdade (tarefa 70).
- **Início em duas composições.** O desenho "Início — onboarding em andamento" não tem os quatro indicadores,
  os comunicados nem os aniversariantes do Início 62:38, e deixa uma faixa vazia embaixo. É preciso decidir se o
  card de onboarding entra no topo do Início existente ou o substitui (tarefa 68).
- **Menu lateral por grupo.** O Design System novo documenta o rótulo de grupo em caixa alta (por exemplo
  "EQUIPE", para o Gestor, com Minha equipe e Delegações). O menu do `app.py` ainda não tem grupos (tarefa 65).

## Privacidade e Documentos (10/10/2026)

Construção das tarefas 5, 26 a 28, 59, 62, 67, 68 e 70. Evidência em
`docs/evidencias/frontend-privacidade-documentos.md`.

### Divergências da revalidação, resolvidas

- **Numeração dos fluxos (tarefa 69).**
  - Regras virou F40 e o índice não tem mais código repetido.
  - No aviso, os códigos de finalidade saíram da tela. No documento, ficaram numa coluna "Registro", que não aparece no app. Essa coluna substitui a proposta de "Finalidade 1…19".
- **IP e dispositivo (tarefa 70).** Decidido gravar, e spec, aviso e backend passam a dizer a mesma coisa.
  - O login grava o IP e um dispositivo resumido ("Chrome no Windows", nunca o user agent inteiro). O IP também vai para a auditoria do `login_sucesso`.
  - Como o Xano só vê o servidor do Streamlit, o frontend repassa os dois dados (`st.context`).
  - Guarda de 6 meses, com a limpeza da rotina diária que já existia.
- **Início em duas composições (tarefa 68).** Decidido em 10/10: o card fica no topo do Início existente.

### Aviso de privacidade: uma fonte só

- A tela lê `docs/lgpd/aviso-de-privacidade.md` (`frontend/aviso_privacidade.py`). Assim, documento, Figma e app mostram o mesmo texto.
- Do arquivo, a tela deixa de fora só a nota da documentação e a coluna "Registro". Os links viram texto simples e o negrito fica só nos rótulos, como no Figma.
- O backend não registra a leitura do aviso, então "lida por você em…" (285:1073 e 286:878) não aparece. A tela mostra a versão.

### Menu da conta e Configurações

- O chip do nome abre o menu 198:158: perfil, "Configurações" e "Sair da conta". "Sair da conta" chama `auth/logout`.
- Configurações abre na aba Privacidade. Segurança e Notificações aparecem como "em construção".

### Documentos: estados do anexo (tarefa 62)

- O backend verifica o link no envio e grava `estado_verificacao` = "liberado" ou "bloqueado", com `motivo_bloqueio`. "enviado" e "em_verificacao" não chegam a ficar gravados.
- Decisão: a tela mostra o selo do `status` do documento. Só quando o arquivo é bloqueado ela troca o selo por "Arquivo bloqueado" e mostra o motivo, porque é o único estado do anexo que pede uma ação da pessoa (enviar outro link). A spec não muda.
- Figma: linha "CNH — Arquivo bloqueado" em 41:26 e 108:541.
- O documento entra por link: o modal 309:1591 (e 313:1573 e 310:1438) passou a ter "Link do arquivo". O modal antigo com "Arraste o arquivo" (222:175, 225:2733 e 249:2032) ficou desatualizado; a referência é o 309:1591.
- "Documentos pendentes" (309:1249) aparece no topo da tela Documentos enquanto houver pedido do RH em aberto.

### Modais no Streamlit

- Os modais (`st.dialog`) ficam abertos por uma marca em `st.session_state`. Por isso continuam na tela quando o app inteiro roda de novo e podem ser testados com o AppTest.
- O tema base do app é escuro, por causa da tela Entrar, então `theme.py` pinta os modais e o menu da conta com as cores claras do protótipo.
