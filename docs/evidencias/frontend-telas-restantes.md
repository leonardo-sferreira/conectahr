# Telas restantes do frontend (tarefas 64, 65, 56, 52, 9, 10, 53, 46, 50, 12, 39 e 40)

**Data:** 21/11/2026. **Change:** `concluir-frontend-streamlit`. Prints em `frontend-telas-restantes/`, tirados de uma
prévia sem rede com dados fictícios.

## O que entrou

| Tarefa | Tela | Figma | Endpoints | Teste sem rede |
|---|---|---|---|---|
| 64 | Rotina diária (menu RH e Admin) | 289:900, 289:1190, 289:1477, 290:1164 | `status_operacional`, `rotinas/processar_diarias`, `auditoria` | `testar_rotina_sessoes.py` |
| 65 | Sessões ativas (menu Admin) | 249:6819 | `admin/sessoes_ativas` GET e `admin/sessoes/{id}/encerrar` POST (novos) | `testar_rotina_sessoes.py` (40/40) |
| 56 | Calendário (pelo "Calendário da equipe" de Férias) | 233:2394 | `calendario` GET (férias agora só com nome, período e status) | `testar_calendario.py` (20/20) |
| 52 | Aba Departamentos da Estrutura da empresa | 249:6993 | `listar_departamentos`, `departamentos` POST, `departamentos/{id}` PATCH, `.../status`, `.../gestor` | `testar_departamentos.py` (21/21) |
| 9, 10 | Pendências do Início | 62:38 | `central_de_tarefas` | `testar_inicio.py` (17/17) |
| 53 | Ficha: Editar cadastro, Mudar cargo ou salário, linha do tempo, onboarding | 243:580 | `colaboradores/{id}` PATCH, `.../vinculo` PATCH, `.../timeline`, `.../onboarding` | `testar_cadastro.py` (129/129) |
| 46 | Aba Comunicados do RH: publicar e arquivar | 245:594 | `comunicados` GET e POST, `comunicados/{id}/arquivar` POST (novo) | `testar_faq.py` (36/36) |
| 50 | Usuários e perfis: Editar nome e e-mail | 246:612 | `usuarios/{id}` PATCH | `testar_cadastro.py` |
| 12 | Central: atalhos para Conferência, Desligamentos e Minha equipe | 436:1142 | `central_de_tarefas` | `testar_decisoes.py` (68/68) |
| 39 | Foco visível em todo controle | Design System | — | teste no Chrome (abaixo) |
| 40 | Seis estados de UI em todas as páginas | — | — | `auditar_estados_ui.py` (51 páginas, 0 falta) |

## Mudanças no backend

- **`admin/sessoes_ativas` GET e `admin/sessoes/{id}/encerrar` POST:** só para o Admin. A lista não traz IP. O endpoint
  de encerrar recusa a sessão do próprio token e grava `encerrar_sessao_admin` na auditoria.
- **`comunicados/{id}/arquivar` POST:** RH e Admin. Faz `ativo = false`, sem apagar nada, e grava
  `arquivar_comunicado` na auditoria. Arquivar de novo é recusado.
- **`calendario` GET:** antes devolvia as férias com `observacao_colaborador` e `observacao_rh` para os colegas do
  departamento. Agora devolve só `id`, `colaborador_id`, `nome`, `data_inicio`, `data_fim` e `status`. Nenhuma tela usava
  esses campos; as que já existiam leem só os feriados. Antes de publicar, conferi que a versão no ar era igual à do git
  (só mudava a quebra de uma linha).

## Verificado por HTTP com login (21/11/2026, contas de teste Admin e Colaborador)

**Sessões ativas:**
- o Admin recebe 200, com as duas sessões abertas, a própria marcada e os campos sem IP;
- o Colaborador recebe 403 tanto para listar quanto para encerrar;
- encerrar a própria sessão dá 400 ("use Sair");
- uma sessão que não existe dá 404.

**Rotina diária:**
- o `status_operacional` não tinha nada pendente; executei duas vezes e as duas voltaram zeradas;
- o Colaborador recebe 403;
- a última execução aparece na auditoria filtrada, no horário de Brasília.

**Calendário:** o Admin e o Colaborador recebem 200, com 40 feriados. Não havia férias aprovadas para conferir os
campos novos.

**Departamentos:**
- o Admin lista os 15 (200) e o Colaborador recebe 403;
- criar com a descrição vazia volta "Missing param: descricao", então a tela passou a exigir a descrição (ou a sigla);
- o Colaborador recebe 403 ao mudar a situação.

**Início:** os campos que a tela lê existem na resposta real da `central_de_tarefas` (Admin e Colaborador). A soma
agora inclui as ausências, as avaliações da equipe e os pedidos LGPD perto do prazo, que faltavam.

**Gravações, com a conta RH (21/11/2026, 23/23):**
- **Comunicados:**
  - o RH publicou um comunicado de teste, só para o perfil RH e vigente só nesse dia;
  - o comunicado apareceu ativo na lista e foi arquivado;
  - depois de arquivado, sumiu dos comunicados de quem estava no público;
  - arquivar de novo deu 400, e um comunicado inexistente deu 404.
  - Ficou no banco, arquivado.
- **Usuários:**
  - o RH trocou o nome da conta Colaborador de teste e depois voltou ao original;
  - editar a conta do Admin foi recusado ("só contas de colaboradores").
- **Ficha:**
  - o RH trocou o telefone da ficha de teste, conferiu e voltou ao original;
  - a linha do tempo respondeu 200;
  - um vínculo com data anterior à admissão foi recusado sem gravar.
  - O caminho que grava o vínculo não foi testado por HTTP, porque cria um registro permanente no histórico.
- **Departamentos:**
  - o RH criou "Teste automatizado" e editou o nome;
  - trocar o gestor por alguém de fora do departamento foi recusado;
  - em seguida inativei o departamento, que ficou no banco como inativo.
  - Trocar o gestor de fato precisa de uma conta Gestor do mesmo departamento e não foi testado.

**Ainda sem HTTP:** encerrar a sessão de outra conta, porque derruba a sessão de quem está logado.

## Acessibilidade (tarefa 39)

- **Foco:**
  - Antes, só os botões e os campos de texto tinham contorno de foco, em âmbar #F5A623 (2:1 sobre o branco, abaixo dos
    3:1 da WCAG 1.4.11).
  - Agora todo controle tem o contorno da variável `--crh-foco`: caixa de seleção, área de texto, número, data,
    checkbox, toggle, rádio, abas, link, download e expansor.
  - No tema claro é #A15C07 (5,2:1 no branco, 4,9:1 no marfim, 3,4:1 no menu grafite). No escuro é #F5A623 (8,8:1).
- **Teste no Chrome:**
  - Com Tab a partir da busca das Sessões ativas, o foco foi para o seletor de perfil.
  - O contorno medido foi `2px solid rgb(161, 92, 7)`; print em `12-foco-teclado.png`.
- **Rótulo do checkbox e do toggle soltos na página:** herdavam o texto claro do tema base escuro (#ECEAE4 sobre o fundo
  claro, quase invisível no Calendário e no "Mostrar o histórico" da Conferência). Agora usam grafite no claro e
  #F2F2F0 no escuro.
- **Contraste:** `medir_contraste.py` continua com 0 pares abaixo de 4,5:1.

## Estados de UI (tarefa 40)

- **Script:** `tools/auditar_estados_ui.py`, que entrou no CI, procura em cada `pagina_*.py` o sinal de cada um dos 6
  estados: carregando, vazio, sucesso, erro, bloqueado e permissão negada.
- **Dispensas:** quando um estado não se aplica (página de qualquer perfil, só de leitura, ou sem ação que dependa de
  condição), a dispensa fica no próprio script, com o motivo.
- **Faltas reais corrigidas:**
  - as abas de Ciclos de avaliação buscavam dados sem indicar o carregamento;
  - o Canal de denúncias enviava e consultava sem indicar o carregamento.

## Diferenças do Figma

**Rotina diária:**
- a linha "Avisos do dia" (convites e avisos de prazo), que a rotina faz e o Figma não lista;
- o botão "Ver o que será feito" recalcula a lista;
- o rodapé diz "horário de Brasília".

**Sessões ativas:**
- não há a coluna "Local" nem o IP, porque a localização não é guardada e o IP fica de fora por minimização;
- não há o quadro "Acesso fora do comum", porque o backend não detecta acesso suspeito.

**Calendário:**
- não há prazos (autoavaliação, fechamento do ponto), porque não há uma fonte única para eles;
- abre por Férias, já que o Figma não põe o Calendário no menu.

**Departamentos:**
- a sigla fica na descrição;
- não há os quadros "Próximos feriados" e "Organograma" embaixo da lista, porque os feriados têm aba própria.

**Comunicados:** não mostram o autor nem têm "Editar", porque o backend não tem a edição e o GET só traz o id de quem
publicou.

## Achado corrigido (tarefa 86)

`colaboradores/{id}/timeline` GET devolvia as linhas inteiras do histórico profissional, com salário, também ao Gestor do
departamento e à própria pessoa, e as férias com as observações.

**O que mudou:** a resposta agora é montada campo a campo.
- **RH e Admin:** o histórico completo, com salário, motivo e as situações de eSocial e CTPS.
- **Gestor e a própria pessoa:** só tipo, datas, cargo, departamento, nível, contrato e jornada.
- **Férias, para todos:** só período e dias.

**Como foi verificado:**
- Conferi a paridade com a versão no ar antes de publicar.
- Por HTTP com a conta RH, a resposta foi 200.
- Como ninguém tem histórico no banco hoje (o vazamento não expôs dados reais), conferi os dois recortes no Xano com uma
  função temporária e dados fictícios. Apaguei a função depois.
