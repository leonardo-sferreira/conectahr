# Figma × Streamlit: o que falta alinhar

**Situação em 13/10/2026.** O protótipo do Figma (`fph1M5tB4rA4gqfIysSmkn`) é a referência visual do projeto
(AGENTS.md, seção 6). Algumas mudanças foram pedidas e construídas no Streamlit enquanto o MCP do Figma estava
fora do ar, ou depois de o Figma ter sido desenhado. Nesses casos, **a tela do Streamlit é a versão mais
recente** e o Figma precisa ser atualizado a partir dela. A atualização do Figma ficou para depois, por decisão
do usuário (13/10/2026).

## Telas em que o Streamlit está à frente do Figma

| Tela | Nó no Figma | O que o Streamlit já tem e o Figma não | Origem |
|---|---|---|---|
| Organograma | 224:3593 | Cartões em coluna: superior direto em cima, a pessoa em destaque no meio e a equipe embaixo, ligados por linhas; cada cartão só com nome, cargo e área; clicar sobe ou desce na hierarquia; "Ir ao topo" e "Minha posição"; sem "Ver detalhes" | Pedido do usuário com imagem de referência (13/10); PR #47 |
| Documentos: modal "Enviar documento" | 309:1591 (escuro 313:1573) | Campo "Arquivo" (PDF, JPG ou PNG, até 10 MB; foto pelo celular) no lugar de "Link do arquivo" | Change `anexo-de-arquivos`, tarefa 1.1; PR #48 |
| Documentos: modal "Enviar documento" (campos) | 309:1591 (escuro 313:1573) | Campos de cada tipo de documento: ao escolher o tipo, aparecem só os campos dele (ex.: RG com número, órgão emissor, UF e data de expedição; CPF só com o número); a conferência do RH mostra os dados informados | Change `campos-por-tipo-de-documento` |
| Conferência de documentos | 418:1108 e 418:1461 | Seta "Ver dados e arquivo" em cada linha, com os dados preenchidos e o arquivo pronto para abrir; regras de documentos obrigatórios agrupadas por contrato (38 pré-definidas) | PR #53; change `documentos-obrigatorios-por-contrato` |
| Colaboradores: ficha | 243:580 | Ficha com dados pessoais, endereço, vínculo e conta bancária (mascarada), documentos enviados com a seta de dados e arquivo, e "Baixar ficha em PDF" | Pedido do usuário (13/10/2026) |
| Conferência: aba "Aceitos" | 418:1108 | Documentos aprovados com histórico (vencidos e substituídos) e filtros por pessoa e tipo | Pedido do usuário (13/10/2026) |
| Tipo de acesso: admissão, Criar acesso, ficha e Usuários e perfis | 243:1075, 246:1245, 243:580 e 246:612 | "Tipo de acesso" na admissão e no Criar acesso (o RH também escolhe; outro perfil vira pedido com justificativa); na ficha, o acesso da conta, "Alterar acesso" (Admin) e "Solicitar alteração de acesso" (RH); em Usuários e perfis, "Pedidos de alteração de acesso" com Aprovar, Recusar e o histórico | Change `pedido-de-acesso` |
| Férias: aba "Férias da equipe" | 40:22 (sem nó próprio) | Calendário do mês com o nome de quem da equipe está de férias em cada dia (verde aprovada, âmbar em análise, "+N"), "Alertar a partir de" com borda vermelha no dia lotado, indicadores e a lista do mês | Change `calendario-ferias-da-equipe` |
| Ponto: Mês (planilha) | 464:826 (escuro 468:1603) | Data completa (dd/mm/aaaa); resumo com horas positivas e horas negativas, sem o saldo único e sem o cartão de atestados; pedido de ajuste pela célula da marcação (Ent. 1, Saí. 2…), com "Corrigir horário" também para a marcação incluída (I); nenhum ajuste no dia de hoje | Change `ponto-rep-p-e-ferias-clt`, tarefas 9.6 a 9.8 (D15 a D18) |
| Trajetória: modais | 64:42 (sem nó dos modais) | "Responder avaliação" (nota de 1 a 5 por competência, Salvar e Enviar com confirmação), "Contestar avaliação", "Check-in da meta" e "Progresso do PDI"; blocos "Para você avaliar" e "Avaliações recebidas" (com a resposta do RH à contestação); no PDI, "Previsto para" no lugar de "Check-in previsto para" e "Próximo encontro em" (o PDI só tem o prazo) | Change `trajetoria-do-colaborador` |
| Pagamento (RH e Admin) | 70:46, 236:357 e 236:594 | Duas telas: "Pagamento" (menu pessoal) mostra a todos, inclusive RH e Admin, só os próprios holerites e informes; "Lançamento de pagamentos" (grupo RH do menu) tem as abas, os filtros, Lançar e Substituir | Pedido do usuário (20/10/2026) |
| Benefícios | — | Construída sem conferência, com o Figma fora do ar. Desde 13/10/2026: o colaborador vê só "Benefícios ativos" e um item por benefício (formato da FAQ) com descrição, links e materiais; o RH tem "Editar" no Catálogo com links e materiais | `pagina_beneficios.py`; change `apresentacao-de-beneficios` |
| Folha de ponto (Gestor e RH) | — | Tela construída sem conferência, com o Figma fora do ar | `pagina_folha_ponto.py` |
| Solicitações ao RH | 225:5299 e 206:1072 | Construída sem conferência, com o Figma fora do ar | `pagina_solicitacoes.py` |

## Diferenças conhecidas e aceitas (o backend não tem o dado)

| Tela | Diferença |
|---|---|
| Comunicados e FAQ (217:154, 245:594) | Sem as abas de categoria do comunicado (RH, TI, Benefícios): o comunicado não tem categoria no backend |
| Férias (40:22) | Resolvido em 13/10/2026: os cartões mostram saldo, períodos e dias vendidos, e o pedido tem "Vender dias". Falta conferir com a seção 22 do Figma (466:833 e 466:1171) |
| Ponto: cabeçalho | O horário contratual mostra a jornada da regra do contrato (horas por dia e por semana), e não um horário de entrada e saída |

## Modo escuro

A página "Protótipo — Dark" ainda não tem todas as seções (tarefas 63 e 75 da change
`concluir-frontend-streamlit`). No Streamlit, o tema escuro já vale para todas as telas.

## Telas desenhadas no Figma e ainda não construídas no Streamlit

Auditoria, Regras (instrumentos normativos e overrides), Rotina diária e
Retenção e anonimização, Reconhecimentos, Pesquisa de clima, Indicadores, Desligamento, Delegações e Minha
equipe. Os endpoints existem no backend; as tarefas estão na change `concluir-frontend-streamlit`.
