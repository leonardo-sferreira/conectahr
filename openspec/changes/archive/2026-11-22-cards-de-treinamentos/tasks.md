# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil. As evidências vão para `docs/evidencias/cards-de-treinamentos.md`, sem dado pessoal.

## 1. Tela

- [x] 1.1 Figma, antes de codar, nos temas claro e escuro e na tela estreita. Verificar: print dos nós.
  - "Meus treinamentos — cards": a grade, os filtros e o estado vazio;
  - "Treinamento expandido": vídeo, PDF e apresentação;
  - o modal do RH com "Tipo de conteúdo" e "Capa";
  - o card próprio (D4).
- [x] 1.2 `treinamentos_modelo.py`: a situação dos cards, os filtros, a capa automática e o corte da descrição (D3, D4). Verificar: regras em `tools/testar_treinamentos.py`.
- [x] 1.3 "Meus treinamentos" em cards, com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada) e uma coluna na tela estreita (D4). Verificar: `tools/testar_treinamentos.py` e o print no Chrome com 390 px de largura.
- [x] 1.4 O detalhe com "Voltar" mantendo o filtro, o visualizador por tipo e a conclusão de leitura com a confirmação (D5, D6). Verificar: `tools/testar_treinamentos.py`.
- [x] 1.5 O modal do RH com o tipo, a capa e o arquivo ou link (D7). Verificar: `tools/testar_treinamentos.py`.

## 2. Integrar

- [x] 2.1 Os campos `conteudo_tipo`, `conteudo_url`, `conteudo_path` e `capa_path` em `treinamento`, e `aberto_em` em `treinamento_progresso` (D1, D6). Verificar: dry-run só com `ADD_FIELD`; os treinamentos atuais viram `video`.
- [x] 2.2 O bucket privado `treinamentos` e `treinamentos/arquivos/envio` POST, só RH e Admin (D2). Verificar: `checar_endpoints`; o Colaborador recebe 403.
- [x] 2.3 `treinamentos` POST e `{id}` PATCH com o tipo, as validações de coerência e os hosts aceitos (D1, D7). Verificar: a 3.1.
- [x] 2.4 `meus_treinamentos` GET com os `cards`, e `meus_treinamentos/{id}/conteudo` GET com a URL assinada, só para o público (D2, D4). Verificar: a 3.2.
- [x] 2.5 `meus_treinamentos/{id}/abrir` POST e `concluir` por tipo, com a auditoria `concluir_treinamento_leitura` (D6). Verificar: a 3.3.

## 3. Testar

- [x] 3.1 HTTP, RH:
  - **passa:** cria um treinamento de PDF (arquivo) e um de apresentação (link do Slides);
  - **falha:** um PDF com campos de vídeo e uma apresentação com link de outro site dão 400; o Colaborador e o Gestor recebem 403.
- [x] 3.2 HTTP, cards:
  - **passa:** a pessoa do público vê os três tipos com a capa, e a URL do conteúdo abre;
  - **falha:** a pessoa fora do público recebe 404 no `conteudo`.
- [x] 3.3 HTTP, conclusão:
  - **passa:** o PDF conclui depois de `abrir` e `confirmo_leitura`, com validade;
  - **falha:** sem `abrir`, ou sem a confirmação, dá 403; o vídeo continua recusando abaixo do mínimo.
- [x] 3.4 `docs/regras-de-negocio.md` (seção 21) e `docs/lgpd/operadores.md` atualizados depois da implementação. Verificar: `openspec validate cards-de-treinamentos`.

## Notas da implementação (21/11/2026)

Evidências em `docs/evidencias/cards-de-treinamentos.md`.

- **1.1:** Figma seção 23, claro `633:1470` e escuro `637:1591`.
- **1.2 a 1.5:** `tools/testar_treinamentos.py` passa 85 de 85. A grade foi conferida no Chrome em 1440, 1000 e 390 px, e o modal com o envio de um PDF e de uma capa.
- **2.1 a 2.5:** publicados no Xano. `checar_endpoints` passa 306 de 306.
- **2.2:** o bucket privado foi criado e conferido:
  - o PDF assinado abre embutido;
  - sem o token, dá 400;
  - HTML é recusado (415).
  O 403 do Colaborador fica para a 3.1.
- **Defeito corrigido:** `meus_treinamentos` devolve `capas` como lista de `{caminho, url}`. O mapa do `assinar_treinamentos` aninha no ponto da chave.
- **Revisão independente:** o defeito do `arquivo: true` no detalhe do PDF foi corrigido, junto com os outros achados. As pendências estão na evidência.
- **3.1 a 3.3 (22/11/2026):** testes por HTTP no Xano real, com as contas Admin, RH e Colaborador e mais o Gestor (a conta Colaborador promovida só durante o teste): 29 de 29 verificações, além dos dois 403 do Gestor. Detalhes na evidência.
