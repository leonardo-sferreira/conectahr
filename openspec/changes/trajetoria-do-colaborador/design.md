# Design

## Context

Ver proposal.md (Why). A avaliação liga o avaliado (`avaliacao.colaborador_id`) ao avaliador (`avaliacao.user_id`), com a relação (`autoavaliacao`, `gestor`, `par`, `subordinado`, `rh`). `minhas_avaliacoes` filtra por `user_id`, ou seja, só o que a pessoa preenche. `avaliacoes/{id}` GET já deixa o avaliado ler uma avaliação **enviada** sobre ele. O plano gratuito do Xano aceita 10 requisições a cada 20 s.

## Goals / Non-Goals

**Goals:** a tela do Figma 64:42 com dados reais, em uma leitura por carregamento; as ações sobre os endpoints de escrita que já existem.

**Non-Goals:** mudar regra de escrita, de status ou de permissão dos endpoints existentes.

## Decisions

### D1. Um endpoint agregado para a tela

`minha_trajetoria` GET devolve tudo o que a tela mostra. Alternativa descartada: chamar `meu_perfil_colaborador`, `colaboradores/{id}/plano_carreira`, `minhas_avaliacoes`, `minhas_metas`, `meu_pdi`, `meus_reconhecimentos_recebidos` e `ciclos_avaliacao` separados. Seriam 7 chamadas, além de `auth/me` e do sino, o bastante para bater no limite de requisições (o mesmo problema do modal Admitir em 20/10/2026), e ainda faltariam o 360 sobre a pessoa e os nomes. Só leitura, sem auditoria, como as outras consultas da pessoa sobre si mesma.

Conteúdo:
- `nivel_atual`, `proximo_nivel` (l1→l2…l4→l5; l5 não tem próximo) e `competencias_proximo_nivel` (só `id` e `nome`, das ativas);
- `ciclo`: o ciclo `em_andamento` mais recente (`id`, `nome`, `data_fim`), ou nulo;
- `trezentos_e_sessenta` do ciclo: `autoavaliacao` (status), `gestor` (status e nome do avaliador), `pares` (`total` e `enviadas`);
- `a_preencher`: avaliações em que a pessoa é avaliadora e o status é `pendente` ou `em_andamento`, com relação, nome do avaliado e ciclo;
- `recebidas`: avaliações **enviadas** sobre a pessoa (qualquer ciclo), com relação, nota, data e a última contestação (status e resposta do RH);
- `metas` e `pdi`: as que não estão concluídas nem canceladas;
- `reconhecimentos`: os recebidos com status `ativo`, com o nome de quem enviou.

Sem ficha de colaborador vinculada à conta: erro "Nao existe um colaborador vinculado a esta conta.", igual a `minhas_metas`.

### D2. Anonimato dos pares

O Figma mostra "Avaliação de pares — 2 de 3 respondidas". O agregado devolve só a contagem dos pares e, em `recebidas`, a relação sem o nome do avaliador quando é `par` ou `subordinado`. O nome aparece só para `gestor` e `rh`. Risco conhecido: `avaliacoes/{id}` GET, que já existe, devolve o `user_id` do avaliador. A tela não usa esse campo nem o mostra, e o ajuste desse endpoint fica fora desta change.

### D3. Competências da avaliação

`avaliacoes/{id}/competencias` GET: só o avaliador designado (autorização antes de existência). Devolve as competências ativas do nível do avaliado (`colaborador.nivel`). Se esse nível não tiver nenhuma, devolve todas as ativas, para a avaliação não ficar impossível de responder. Inclui as respostas já salvas (nota e comentário), para retomar uma avaliação `em_andamento`. Nota de 1 a 5, como `avaliacoes/{id}/respostas` exige.

### D4. Tela e ações

- Menu "Trajetória" para quem tem `colaborador_id` (a entrada já existe em `app.py` como "em breve").
- Os blocos seguem o Figma 64:42: cartão do plano de carreira, linhas com bolinha e selo para avaliação, metas e PDI, e a lista de reconhecimentos.
- Selos: avaliação Enviada (verde) ou Pendente (âmbar); meta e PDI Atrasada/Atrasado (vermelho) quando o prazo passou e não estão concluídos, senão Pendente (âmbar), ou Em andamento quando já houve progresso.
- Ações (modais com os componentes do `theme.py`, sem nó no Figma, registradas em `docs/figma-pendencias.md`):
  - **Responder avaliação** (bloco "Para você avaliar", aparece só se houver): nota de 1 a 5 por competência, com comentário opcional; "Salvar" grava cada resposta alterada e "Enviar" grava e envia, depois de confirmar que o envio é definitivo.
  - **Contestar** uma avaliação recebida sem contestação aberta: motivo de 5 a 2000 caracteres.
  - **Check-in de meta**: progresso de 0 a 100, comentário, dificuldades e evidência.
  - **Progresso do PDI**: progresso de 0 a 100 e evidência.
- Os 6 estados: carregando (spinner), vazio por bloco, sucesso (toast), erro (alerta com a mensagem do backend), sem ficha (aviso) e permissão negada (mensagem do backend).

## Risks / Trade-offs

- [O agregado faz consultas por item (nomes do avaliador e do remetente)] → as listas da pessoa são pequenas; a consulta é por `db.get` com `output` restrito.
- [Erro de execução no XanoScript não aparece no `checar_endpoints`] → `tools/testar_trajetoria_http.py`, com login de verdade, a rodar depois do push.
- [`avaliacoes/{id}` GET expõe o `user_id` do avaliador par] → registrado em D2; a tela não usa o campo.

## Migration Plan

Push só dos dois arquivos novos (dry-run com 2 `CREATE` e nada mais). Rollback: apagar os dois endpoints no Xano; nada de schema muda.
