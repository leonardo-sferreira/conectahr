# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil, respeitando o limite de 10 requisições a cada 20 segundos (`tools/limite_http.py`). As evidências vão para `docs/evidencias/notificacoes-de-publicacao.md`, sem dado pessoal.

## 1. Tela

- [ ] 1.1 Figma: Configurações → Notificações (213:236) com as linhas "Treinamentos" e "Pesquisas", nos temas claro e escuro, e o e-mail travado com "Em breve" (D6). Verificar: print dos nós.
- [ ] 1.2 Figma: o aviso de treinamento e o convite de pesquisa no painel do sino, com o destino de cada clique. Verificar: print dos nós.
- [ ] 1.3 `configuracoes_modelo.py` e a tela de Notificações com os assuntos novos, com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada). Verificar: `tools/testar_configuracoes.py`.
- [ ] 1.4 `notificacoes_modelo.py`: `treinamento_novo` leva a "Meus treinamentos"; `pesquisa_nova`, à "Pesquisa de clima" ou ao Início (termômetro); `pedido_novo` com recurso `delegacao`, à "Delegações". Verificar: `tools/testar_notificacoes.py`.

## 2. Integrar

- [ ] 2.1 Enums: `notificacao_interna.tipo` (`treinamento_novo`, `pesquisa_nova`) e `preferencia_aviso.assunto` (`treinamentos`, `pesquisas`) (D1, D6). Verificar: dry-run só com `UPDATE` das tabelas.
- [ ] 2.2 `ConectaHR/notificar_publico`, com lote, preferência e sem o autor (D1). Verificar: o teste HTTP da 3.1.
- [ ] 2.3 `treinamentos` POST e `treinamentos/{id}` PATCH chamam a função ao criar ou reativar (D2). Verificar: `checar_endpoints` e a 3.1.
- [ ] 2.4 `pesquisa_clima.convite_enviado_em`, o disparo em `perguntas` POST e na rotina diária, e o convite por ciclo do termômetro (D3). Verificar: a 3.2.
- [ ] 2.5 `delegacoes` POST avisa o substituto, e `ConectaHR/notificar_decisores` inclui o substituto ativo (D4). Verificar: a 3.3.
- [ ] 2.6 (Opcional) Lembretes `treinamento_vencendo` e `pesquisa_encerrando` na rotina diária (D5). Verificar: duas execuções seguidas da rotina geram os avisos uma vez só.

## 3. Testar

- [ ] 3.1 HTTP, treinamento:
  - **passa:** o RH publica para o departamento X; uma pessoa de X recebe; o RH que publicou não recebe;
  - **falha:** a pessoa de Y não recebe, e a pessoa que desligou "Treinamentos" não recebe.
- [ ] 3.2 HTTP, pesquisa:
  - **passa:** a pesquisa aberta gera o convite uma vez só;
  - **falha:** rodar a rotina de novo não gera outro; marcar o convite como lido não cria participação (a contagem da pesquisa não muda).
- [ ] 3.3 HTTP, decisões: para cada linha da tabela do D4, o decisor certo recebe `pedido_novo` e o autor não recebe. Delegação: o substituto recebe.
- [ ] 3.4 `docs/regras-de-negocio.md`, `docs/preferencias-notificacao.md` e `docs/lgpd/registro-de-operacoes.md` (F16) atualizados depois da implementação. Verificar: `openspec validate notificacoes-de-publicacao`.
