# Design — Delegações do Gestor

## Contexto

Escopo parcial autorizado em 21/10/2026. Referências Figma conferidas pelo MCP: seção `248:2211`,
caminho `248:2225`, tela `248:2235`, composição `248:2463`, modal `248:2465` e Central
`248:2513`/`248:2519`. Reutilizar Streamlit, `theme.py`, tabelas, badges, cartões e `st.dialog`.

## Decisões

1. Somente o perfil Gestor recebe a página/menu nesta tarefa. A lista vem exclusivamente de
   `minhas_delegacoes`; conferir vínculo como titular ou substituto usando `usuario.id`, nunca
   `colaborador_id`. Descartar registros fora desse vínculo e campos fora da apresentação.
2. Cancelada tem precedência quando há `cancelada_em`; depois, datas ISO válidas: Agendada se
   hoje < início, Ativa se início <= hoje <= fim, Encerrada se fim < hoje. Usar data UTC como
   nos consumidores reais do backend, sem persistir estado. Datas inválidas ficam indisponíveis,
   em vez de inventar vigência; informar dados incompletos mantendo registros válidos.
3. Ativas e futuras contém Agendada/Ativa e registros com vigência não disponível; Encerradas
   contém Encerrada/Cancelada. Exibir período, escopo, situação, motivo e direção. Sem catálogo
   autorizado de usuários, usar Substituto não disponível/Titular não disponível. Não consultar
   usuários, organograma, colaboradores ou outro módulo para tentar resolver esses IDs.
4. Nova delegação abre um modal informativo bloqueado: seleção de substituto e criação
   indisponíveis, sem entrada manual de IDs, datas fictícias ou POST. Não criar wrapper sem uso
   para a criação. A diferença em relação ao modal completo é intencional e fica documentada.
5. Cancelar só aparece para o titular e quando `cancelada_em` é nulo. Vale também para vencidas,
   como o contrato permite. Atualizar a lista antes de tentar cancelar; o POST continua sendo a
   autoridade final. Não permitir cancelamento de recebida, exclusão, edição ou reativação.
   Após confirmação, invalidar cache e abrir Encerradas para mostrar Cancelada. Falha no GET
   posterior preserva a informação da operação confirmada e mostra erro, sem inventar lista vazia.
6. Cache de 20 segundos, restrito ao token/usuário e limpo ao trocar sessão/sair. Falhas não são
   cacheadas como vazio. POST recusado não atualiza estado local. Sanitizar estrutura da resposta,
   escapar textos e exibir somente campos necessários; IDs ficam internos.
7. Manter a estrutura visual do F17. Acrescentar direção/motivo na célula da pessoa. Os cartões
   explicam as limitações reais; não copiar a promessa de entrega de pedidos à Central.

## Dependências de backend (não concluídas)

**Figma:** permite selecionar substituto, criar e encaminhar decisões à Central, com vários escopos.
**Backend atual:** criação exige `substituto_user_id`, sem catálogo autorizado ao Gestor; Central
não incorpora delegações. Só férias e correção de ponto têm consumidores; `todas` só é reconhecido
nesses consumidores. Ausência, documento, desligamento e solicitação ao RH não ganham esse efeito.
Há divergência entre superior direto na hierarquia normal e gestor departamental na delegação.
Não corrigir isso no frontend. Auditoria é registrada no backend, mas a consulta é RH/Admin e
não há vínculo estruturado da delegação em todas as decisões; não criar histórico local.

## Verificação

Testes de modelo/contratos e AppTest com API fictícia: perfil, menu, direções, estados e limites
UTC, vazio, resposta parcial/malformada, cancelamento confirmado/recusado/repetido, recuperação de
falha após POST, sessão, privacidade e criação bloqueada. Regressões pedidas: decisões, férias,
folha/ponto, login, Minha equipe e Avaliações da equipe. Sintaxe, OpenSpec e prévia Streamlit/Chrome
com dados fictícios e comparação ao Figma. HTTP real fica não verificado sem sessão disponibilizada.
