# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil, respeitando o limite de 10 requisições a cada 20 segundos (`tools/limite_http.py`). As evidências vão para `docs/evidencias/notificacoes-de-publicacao.md`, sem dado pessoal.

## 1. Tela

- [x] 1.1 Figma: Configurações → Notificações (213:236) com as linhas "Treinamentos" e "Pesquisas" (D6). Verificar: print dos nós.
  - **Feito (23/10/2026):** 569:874 e 569:885, no modo claro. Falta a versão escura.
- [ ] 1.2 Figma: o aviso de treinamento e o convite de pesquisa no painel do sino, com o destino de cada clique. Verificar: print dos nós.
- [x] 1.3 `configuracoes_modelo.py` e a tela de Notificações com os assuntos novos, com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada). Verificar: `tools/testar_configuracoes.py`.
  - **Feito (23/10/2026):** 23/23; a coluna de e-mail mostra "Sem e-mail" nos dois assuntos novos.
- [x] 1.4 `notificacoes_modelo.py`: `treinamento_novo` leva a "Meus treinamentos"; `pesquisa_nova`, à "Pesquisa de clima" ou ao Início (termômetro); `pedido_novo` com recurso `delegacao`, à "Delegações". Verificar: `tools/testar_notificacoes.py`.
  - **Feito (23/10/2026):** 22/22; os atalhos `ir_meus_treinamentos`, `ir_pesquisa_clima` e `ir_delegacoes` entraram no `app.py`.

## 2. Integrar

- [x] 2.1 Enums: `notificacao_interna.tipo` (`treinamento_novo`, `pesquisa_nova`) e `preferencia_aviso.assunto` (`treinamentos`, `pesquisas`) (D1, D6). Verificar: dry-run só com `UPDATE` das tabelas.
- [x] 2.2 `ConectaHR/notificar_publico`, com lote, preferência e sem o autor (D1). Verificar: o teste HTTP da 3.1.
- [x] 2.3 `treinamentos` POST e `treinamentos/{id}` PATCH chamam a função ao criar ou reativar (D2). Verificar: `checar_endpoints` e a 3.1.
- [x] 2.4 `pesquisa_clima.convite_enviado_em`, o disparo em `perguntas` POST e na rotina diária, e o convite por ciclo do termômetro (D3). Verificar: a 3.2.
- [x] 2.5 `delegacoes` POST avisa o substituto, e `ConectaHR/notificar_decisores` inclui o substituto ativo (D4). Verificar: a 3.3.
  - **Feito (23/10/2026), 2.1 a 2.5:**
    - publicados; `checar_endpoints` 275, 0 falhas;
    - o publicado antes foi conferido igual ao `master` (só formatação);
    - o convite de pesquisa saiu da rota de perguntas para a leitura do Início e a rotina diária (ver o D3);
    - o `db.bulk.add` não existe nesta instância (ver o D1).
- [ ] 2.6 (Opcional) Lembretes `treinamento_vencendo` e `pesquisa_encerrando` na rotina diária (D5). Verificar: duas execuções seguidas da rotina geram os avisos uma vez só.

## 3. Testar

As três primeiras rodam juntas em `tools/testar_notificacoes_publicacao_http.py`, que pede uma conta do RH ou Admin e uma de Colaborador. A pesquisa de clima (3.2) depende de uma pesquisa real abrindo; o script confere o convite do termômetro, que usa a mesma função.


- [ ] 3.1 HTTP, treinamento:
  - **passa:** o RH publica para o departamento X; uma pessoa de X recebe; o RH que publicou não recebe;
  - **falha:** a pessoa de Y não recebe, e a pessoa que desligou "Treinamentos" não recebe.
- [ ] 3.2 HTTP, pesquisa:
  - **passa:** a pesquisa aberta gera o convite uma vez só;
  - **falha:** rodar a rotina de novo não gera outro; marcar o convite como lido não cria participação (a contagem da pesquisa não muda).
- [ ] 3.3 HTTP, decisões: para cada linha da tabela do D4, o decisor certo recebe `pedido_novo` e o autor não recebe. Delegação: o substituto recebe.
- [x] 3.4 `docs/regras-de-negocio.md`, `docs/preferencias-notificacao.md` e `docs/lgpd/registro-de-operacoes.md` (F16) atualizados depois da implementação. Verificar: `openspec validate notificacoes-de-publicacao`.
  - **Feito (23/10/2026):** seção 23 das regras de negócio, o documento de preferências e a F16.
