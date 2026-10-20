# Design

## Context

Ver proposal.md. Decisões do usuário (20/10/2026): o RH cadastra as perguntas; janelas em fevereiro, junho e outubro; autoavaliação nas etapas 2 e 3; o gestor acompanha e registra feedback em cada etapa; vale para todas as pessoas da empresa, qualquer que seja o perfil. O plano do Xano não tem tarefas agendadas e aceita 10 requisições a cada 20 s.

## Goals / Non-Goals

**Goals:** um ciclo por ano, igual para todos; formulário que fecha sozinho pela data; histórico imutável depois do envio; feedback visível às três partes.

**Non-Goals:** reaproveitar `ciclo_avaliacao`/`meta_avaliacao`. Eles servem à avaliação 360 e às metas lançadas pelo RH; misturar mudaria o significado dos dados antigos e da Trajetória.

## Decisions

### D1. Ciclo e janelas

Tabela `ciclo_metas`: `ano` (único), e para cada etapa `etapaN_inicio` e `etapaN_fim` (datas). Padrão sugerido na tela: 01/02 a fim de fevereiro, 01/06 a 30/06 e 01/10 a 31/10. Validações: as datas são do próprio ano, cada fim é igual ou depois do início e cada etapa começa depois do fim da anterior.

- A etapa está **aberta** quando `inicio <= hoje <= fim` (hoje pelo horário de Brasília), **futura** antes e **encerrada** depois. A situação do ciclo é derivada das datas: "Não iniciado", "Etapa N aberta", "Entre etapas" e "Encerrado".
- O RH (e o Admin) cria o ciclo e altera as datas só **antes** da etapa 1 abrir; depois disso as datas ficam fixas (todos respondem no mesmo período). Criação e alteração são auditadas.

### D2. Perguntas

Tabela `pergunta_meta` (`texto`, `orientacao`, `ordem`, `ativa`). O RH cria, edita e desativa (sem excluir). Se não houver nenhuma, a tela oferece "Usar as perguntas sugeridas" (quatro: entrega, qualidade, desenvolvimento e colaboração). O formulário guarda o **texto da pergunta** em cada resposta, para que editar a pergunta depois não mude o histórico. As perguntas de um formulário são as ativas no momento da primeira resposta da etapa 1.

### D3. Formulário, respostas e envio

- `formulario_meta`: um por pessoa e ciclo (`ciclo_metas_id`, `colaborador_id`, `etapaN_enviada_em`).
- `resposta_meta`: uma por pergunta do formulário (`pergunta_meta_id`, `pergunta_texto`, `meta`, `alcancado_etapa2`, `autoavaliacao_etapa2`, `alcancado_etapa3`, `autoavaliacao_etapa3`). Autoavaliação: `abaixo`, `dentro` ou `acima` do esperado.
- `meu_ciclo_metas/{ciclo_id}/respostas` POST grava uma resposta da etapa aberta (cria o formulário na primeira). Uma chamada por pergunta, como `avaliacoes/{id}/respostas`: não há precedente de lista em JSON no workspace.
- `meu_ciclo_metas/{ciclo_id}/enviar` POST fecha a etapa aberta: exige o texto em todas as perguntas (e a autoavaliação nas etapas 2 e 3). Depois do envio, ou com a janela encerrada, nada muda.
- Etapas 2 e 3 só podem ser preenchidas se a etapa 1 foi enviada (sem meta não há o que acompanhar). A etapa 3 não depende da 2.
- Quem preenche: a conta com ficha de colaborador, sobre a própria ficha. O perfil não importa.
- Toda gravação e todo envio são auditados, sem o texto das respostas.

### D4. Feedback

Tabela `feedback_meta` (`formulario_meta_id`, `etapa`, `autor_user_id`, `texto`), só inclusão, sem edição (como os check-ins). Pode registrar: o **superior direto** da pessoa (`superior_colaborador_id`) ou o **gestor do departamento** dela (`departamento.gestor_colaborador_id`), nunca sobre o próprio formulário; só em etapa já enviada; sem prazo. Avisos no sino: ao enviar uma etapa, o superior direto (ou, sem ele, o gestor do departamento) recebe `pedido_novo` (recurso `formulario_meta`); ao receber feedback, a pessoa recebe `avaliacao_disponivel`. Tipos que já existem no enum de `notificacao_interna`, sem mudar o schema.

### D5. Leitura e telas

- `meu_ciclo_metas` GET: os ciclos (o atual primeiro), a situação de cada etapa, as perguntas ativas, o formulário da pessoa com respostas e feedbacks.
- `formularios_meta` GET: RH e Admin veem todos; quem é superior direto ou gestor de departamento vê os da sua equipe. Filtro por ciclo. Traz a pessoa, o departamento e a situação de cada etapa.
- `formularios_meta/{id}` GET: o detalhe, para a própria pessoa, o RH, o Admin, o superior direto e o gestor do departamento.
- Telas: "Metas do ciclo" (a pessoa; aberta pela Trajetória), "Ciclos de avaliação" (grupo RH: abas Ciclos, Perguntas e Formulários) e "Metas da equipe" (grupo Equipe, para o Gestor e para quem é superior direto). O formulário aberto mostra as três etapas, com as respostas e a caixa de feedback de cada uma.

## Risks / Trade-offs

- [Salvar o formulário faz uma chamada por pergunta] → as perguntas são poucas (4 a 8); `api_client` já tenta de novo depois de um 429. Só as respostas alteradas são enviadas.
- [Sem tarefa agendada, ninguém é avisado na abertura da etapa] → a Trajetória mostra "Etapa N aberta até dd/mm" e o bloco fica em destaque.
- [Erro de execução do XanoScript não aparece no checker] → `tools/testar_ciclo_metas_http.py` com login de verdade.

## Migration Plan

Push em duas partes: primeiro as cinco tabelas (só `CREATE`), depois os endpoints (só `CREATE`). Rollback: apagar os endpoints e as tabelas novas; nada existente muda.
