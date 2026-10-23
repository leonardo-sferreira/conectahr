# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil. As evidências vão para `docs/evidencias/cards-de-treinamentos.md`, sem dado pessoal.

## 1. Tela

- [ ] 1.1 Figma, antes de codar, nos temas claro e escuro e na tela estreita. Verificar: print dos nós.
  - "Meus treinamentos — cards": a grade, os filtros e o estado vazio;
  - "Treinamento expandido": vídeo, PDF e apresentação;
  - o modal do RH com "Tipo de conteúdo" e "Capa";
  - o card próprio (D4).
- [ ] 1.2 `treinamentos_modelo.py`: a situação dos cards, os filtros, a capa automática e o corte da descrição (D3, D4). Verificar: regras em `tools/testar_treinamentos.py`.
- [ ] 1.3 "Meus treinamentos" em cards, com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada) e uma coluna na tela estreita (D4). Verificar: `tools/testar_treinamentos.py` e o print no Chrome com 390 px de largura.
- [ ] 1.4 O detalhe com "Voltar" mantendo o filtro, o visualizador por tipo e a conclusão de leitura com a confirmação (D5, D6). Verificar: `tools/testar_treinamentos.py`.
- [ ] 1.5 O modal do RH com o tipo, a capa e o arquivo ou link (D7). Verificar: `tools/testar_treinamentos.py`.

## 2. Integrar

- [ ] 2.1 Os campos `conteudo_tipo`, `conteudo_url`, `conteudo_path` e `capa_path` em `treinamento`, e `aberto_em` em `treinamento_progresso` (D1, D6). Verificar: dry-run só com `ADD_FIELD`; os treinamentos atuais viram `video`.
- [ ] 2.2 O bucket privado `treinamentos` e `treinamentos/arquivos/envio` POST, só RH e Admin (D2). Verificar: `checar_endpoints`; o Colaborador recebe 403.
- [ ] 2.3 `treinamentos` POST e `{id}` PATCH com o tipo, as validações de coerência e os hosts aceitos (D1, D7). Verificar: a 3.1.
- [ ] 2.4 `meus_treinamentos` GET com os `cards`, e `meus_treinamentos/{id}/conteudo` GET com a URL assinada, só para o público (D2, D4). Verificar: a 3.2.
- [ ] 2.5 `meus_treinamentos/{id}/abrir` POST e `concluir` por tipo, com a auditoria `concluir_treinamento_leitura` (D6). Verificar: a 3.3.

## 3. Testar

- [ ] 3.1 HTTP, RH:
  - **passa:** cria um treinamento de PDF (arquivo) e um de apresentação (link do Slides);
  - **falha:** um PDF com campos de vídeo e uma apresentação com link de outro site dão 400; o Colaborador e o Gestor recebem 403.
- [ ] 3.2 HTTP, cards:
  - **passa:** a pessoa do público vê os três tipos com a capa, e a URL do conteúdo abre;
  - **falha:** a pessoa fora do público recebe 404 no `conteudo`.
- [ ] 3.3 HTTP, conclusão:
  - **passa:** o PDF conclui depois de `abrir` e `confirmo_leitura`, com validade;
  - **falha:** sem `abrir`, ou sem a confirmação, dá 403; o vídeo continua recusando abaixo do mínimo.
- [ ] 3.4 `docs/regras-de-negocio.md` (seção 21) e `docs/lgpd/operadores.md` atualizados depois da implementação. Verificar: `openspec validate cards-de-treinamentos`.
