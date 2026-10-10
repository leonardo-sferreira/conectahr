# Evidências — Privacidade e Documentos (tarefas 5, 26 a 28, 59, 62, 67, 68 e 70)

Telas construídas em 10/10/2026 no frontend Streamlit, branch `feature/lgpd-documentos-privacidade`, a partir
dos nós do Figma abaixo.

| Nó do Figma | Tela | Código |
|---|---|---|
| 282:868 | Entrar com o link "Aviso de privacidade →" | `frontend/pagina_entrar.py` |
| 285:874 | Aviso de privacidade sem login | `frontend/pagina_aviso.py` (`pagina_aviso_publico`) |
| 285:1073 | Aviso de privacidade logado | `frontend/pagina_aviso.py` (`pagina_aviso_logado`) |
| 198:158 | Menu da conta (Configurações e Sair da conta) | `frontend/theme.py` (`render_topbar`) |
| 286:878 | Configurações → Privacidade | `frontend/pagina_configuracoes.py` |
| 286:1062 e 286:1092 | Baixar meus dados (escolha e sucesso) | `frontend/pagina_configuracoes.py` |
| 224:2379 | Fazer um pedido | `frontend/pagina_configuracoes.py` |
| 41:26 | Documentos cadastrais (com o estado "Arquivo bloqueado", tarefa 62) | `frontend/pagina_documentos.py` |
| 309:1249 | Documentos pendentes | `frontend/pagina_documentos.py` |
| 309:1591 | Enviar documento (campo "Link do arquivo", tarefa 62) | `frontend/pagina_documentos.py` |

As regras de apresentação ficam em módulos sem Streamlit:
- `frontend/aviso_privacidade.py`: lê o aviso de `docs/lgpd/aviso-de-privacidade.md`;
- `frontend/privacidade_modelo.py`: pedidos, opções do modal, arquivo exportado;
- `frontend/documentos_modelo.py`: selos, linhas pendentes, validação do envio.

## Como repetir

```
python tools/testar_privacidade_documentos.py   # 75 verificações
python tools/testar_login_f01.py                # 52 verificações
python tools/testar_onboarding.py               # 45 verificações
```

Rodam sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 75 de 75, 52 de 52 e 45 de 45.**

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Os 32 parágrafos do `aviso-de-privacidade.md` aparecem na tela, sem os códigos F01–F19, sem a coluna Registro e sem a nota interna (tarefa 59) | ok |
| Sucesso | O link da tela Entrar abre o aviso sem sessão e sem chamar a API; "← Voltar para Entrar" volta | ok |
| Sucesso | Menu da conta: perfil, "Configurações" abre Privacidade, "Sair da conta" chama `auth/logout`, apaga o token e volta a Entrar com aviso | ok |
| Sucesso | Os cinco cartões de Privacidade, a versão do aviso e o encarregado lidos do próprio aviso | ok |
| Sucesso | Botões de aniversariantes e mural mostram o que está gravado; mudar um grava os dois campos (o PATCH exige os dois) | ok |
| Sucesso | "Meus pedidos": só os `privacidade_lgpd`, com "Aberto em…", "responder até…" e o selo da situação | ok |
| Sucesso | "Fazer um pedido": 3 opções do Figma; envia `privacidade_lgpd` com o subtipo e o detalhe; o modal fecha | ok |
| Sucesso | "Baixar meus dados": abrir o modal não exporta nada; "Baixar arquivo" chama `meus_dados?formato=csv` e mostra "Arquivo gerado. O download começou (meus_dados.csv)." | ok |
| Sucesso | Documentos: selos Aprovado, Em análise, Vencido ("Válido até…"), Rejeitado, Substituído ("(anterior)") | ok |
| Sucesso | Documentos pendentes: enviados primeiro, depois os que faltam pelo prazo; pedido cancelado não aparece | ok |
| Sucesso | "Ver" pede o link a `documentos/{id}/arquivo` (auditado) e mostra "Abrir arquivo" | ok |
| Sucesso | "Enviar →" abre o modal com o tipo da pendência; envia tipo, colaborador da sessão e link | ok |
| Vazio | Sem pedidos ("Você ainda não fez nenhum pedido."); sem documentos nem pendências | ok |
| Erro | Erro nas preferências fica no cartão e o resto da tela continua; gravar com erro desfaz o botão | ok |
| Erro | Link sem https é recusado antes da API; domínio recusado pelo backend aparece no modal, que continua aberto | ok |
| Bloqueado | Arquivo bloqueado na verificação: selo "Arquivo bloqueado" e o motivo (tarefa 62); colaborador desligado: mensagem do backend | ok |
| Permissão negada | 403 ao abrir o arquivo vira mensagem, sem derrubar a tela | ok |
| Sem colaborador | Conta de Admin ou RH sem cadastro de colaborador: mensagem em Privacidade e em Documentos, em vez de erro | ok |
| Exclusão (tarefa 28) | Nenhum botão de excluir, apagar ou arquivar na tela, e o `api_client.py` não tem função de exclusão | ok |
| Só dados próprios | `meus_dados` recebe só o token: nenhum endpoint destas telas recebe id de outra pessoa | ok |
| Carregando | Spinner na página e no modal de exportação | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints só do app (dados fictícios), em [`frontend-privacidade-documentos/`](frontend-privacidade-documentos/):

| Print | Compare com |
|---|---|
| `1-entrar-link-aviso` | 282:868 |
| `2-aviso-sem-login` | 285:874 |
| `3-menu-da-conta` | 198:158 |
| `4-configuracoes-privacidade` | 286:878 |
| `5-baixar-meus-dados` | 286:1062 |
| `6-baixar-meus-dados-sucesso` | 286:1092 |
| `7-fazer-um-pedido` | 224:2379 |
| `8-pedido-enviado` | sem nó próprio |
| `9-aviso-logado` | 285:1073 |
| `10-documentos` | 309:1249 e 41:26 |
| `11-enviar-documento` | 309:1591 |

- O download de "Baixar meus dados" começou sozinho no navegador e gerou o arquivo `meus_dados.json`.
- Depois de "Enviar pedido", o pedido novo aparece em "Meus pedidos" como "Recebido", com o prazo de 15 dias.
- "Enviar documentos", na boas-vindas do onboarding e em "Meu onboarding", abre a tela Documentos (fecha a tarefa 68).

## Decisões e diferenças em relação ao Figma

**Aviso de privacidade**
- **Fonte única do texto:** a tela lê `docs/lgpd/aviso-de-privacidade.md`. O teste confere que todo parágrafo do documento aparece na tela.
- **Negrito:** o documento usa negrito para ênfase. A tela, como o Figma, só deixa em negrito os rótulos ("Xano:", "Como exercer:") e a primeira coluna da tabela.
- **"Lida por você em…":** não aparece, nem no aviso logado nem no cartão de Configurações, porque o backend não registra a leitura do aviso. A tela mostra só a versão ("Rascunho de 10/10/2026").

**Configurações**
- **Abas Segurança e Notificações:** já têm desenho (213:142 e 213:236), mas ainda não foram construídas. A tela abre na aba Privacidade.

**Documentos (decisão da tarefa 62)**
- **Link em vez de anexo:** o modal pede o **link** do arquivo, porque o plano do Xano não aceita upload e o backend só aceita `arquivo_url` https de um domínio aprovado. O Figma 309:1591 foi atualizado: o campo "Arquivo" passou a "Link do arquivo", em claro (309:1591), escuro (313:1573) e no fluxo (310:1438).
- **Estados do anexo:** dos quatro estados, só "bloqueado" aparece na tela. Os estados "enviado" e "em verificação" só existem durante o envio, e "liberado" é o normal. O Figma 41:26 (e o escuro 108:541) ganhou a linha "CNH — Arquivo bloqueado".
- **Prazo das pendências:** a linha mostra a observação do RH quando existe, senão "Pedido pelo RH". A data em que o RH fez o pedido não vem do backend (o `created_at` é privado).
- **Modal antigo 222:175:** o modal com "Arraste o arquivo" (e as cópias nos fluxos 225:2733 e 249:2032) ficou desatualizado. A referência é o 309:1591.

**Comportamento do app**
- **Cache de 20 segundos** em `st.session_state` para Documentos e Privacidade (limite do Xano: 10 requisições a cada 20 segundos), como no onboarding. O cache, o link aberto e o arquivo exportado são apagados no fim da sessão.
