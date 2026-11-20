# Design — Avaliações da equipe

## Contexto e referência

Escopo autorizado em 21/10/2026: somente frontend, respeitando o backend atual.
Figma conferido pelo MCP: seção F15 `248:722`, tela `248:744`, modal `248:1019`.
Streamlit, `theme.py`, `st.dialog` e os componentes de tabela existentes; sem outro design system.

## Decisões

1. `minhas_avaliacoes` é a fonte de atribuições. A página do Gestor apresenta somente registros
   com `user_id` igual ao usuário autenticado e `relacao_avaliador = gestor`. O organograma
   enriquece somente nome, cargo e nível, sem criar permissão. Não usar a equipe do F14
   como fonte de autorização. Os endpoints continuam decidindo o acesso a cada operação.
2. `ciclos_avaliacao` alimenta o seletor; ciclos referenciados nas atribuições continuam
   selecionáveis mesmo sem metadados, com identificação pelo ID. Falha nessa consulta ou
   no organograma preserva as atribuições. Falha na fonte principal nunca vira lista vazia.
3. Liderados no ciclo = pessoas distintas nas atribuições não canceladas; enviadas = avaliações
   `enviada`; a fazer = `pendente` ou `em_andamento`. Os números descrevem as atribuições
   do usuário nesse ciclo, não todos os subordinados. Contestações abertas = `—`.
4. Autoavaliação = `—`/Não disponível. Não consultar endpoints do RH, não inferir envio por
   ausência em filas e não impor uma sequência que o backend não consegue confirmar.
   Prazo específico do Gestor não disponível; não apresentar `data_fim` como se fosse esse prazo.
5. Reutilizar `trajetoria_modelo.respostas_alteradas`, `validar_envio` e a escala de notas.
   Competências são consultadas ao abrir; o estado retornado impede edição de enviadas e
   canceladas. Revalidar a atribuição e o estado antes de salvar/enviar. Tratar recusa do backend.
6. Rascunho persiste notas e comentários por competência. Comentário geral só vai em `enviar`;
   informar essa diferença junto ao campo. Depois de gravar, invalidar caches do F15 e da
   Trajetória. Falha parcial mantém o formulário e informa que algumas respostas podem ter
   sido salvas. O envio não é transacional com as gravações por competência.
7. Cache curto por sessão/usuário/token, apagado ao sair, inclusive widgets e seleção do modal.
   Exibir apenas campos profissionais e respostas da própria atribuição; escapar texto da API.

## Divergência de contestações (pendente)

**FIGMA:** Gestor responde contestação e pode manter/revisar nota.

**BACKEND ATUAL:** somente RH/Admin revisa contestação e a revisão não altera a avaliação
original. Sem contrato para decisão, nota revisada ou prazo de resposta. A aba será informativa,
sem consultas proibidas nem botões de revisão. Esta parte não está concluída.

## Verificação

AppTest com API simulada: navegação Gestor, atribuições e recusas, ciclos, rascunho, envio,
quatro estados, competências ausentes, falhas parciais, 401/403, campos sensíveis e indisponibilidade.
Executar suites relacionadas, sintaxe e iniciar Streamlit. Comparar prévia com dados fictícios ao
Figma. HTTP real por perfil depende de sessão autenticada e fica não verificado sem ela.
