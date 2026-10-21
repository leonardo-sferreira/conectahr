# Tasks

## 0. Figma

- [x] 0.1 Desenhar "Meus treinamentos — assistir o vídeo" (557:1383) e "Modal/Novo treinamento — com vídeo" (557:1477) na seção 22 (D5). Verificar: prints dos nós.
  - **Feito (21/10/2026):** modo claro. Falta a versão escura (docs/figma-pendencias.md).

## 1. Backend

- [x] 1.1 Campos de vídeo em `treinamento` e tabela `treinamento_progresso` (D1, D2). Verificar: dry-run com só os `ADD_FIELD` e um `CREATE`.
  - **Feito (21/10/2026):** publicados.
- [x] 1.2 `treinamentos` POST e `{id}` PATCH com o vídeo, `meus_treinamentos` GET com o progresso, `meus_treinamentos/{id}/progresso` e `meus_treinamentos/{id}/concluir` (D1 a D3). Verificar: `checar_endpoints` e dry-run.
  - **Feito (21/10/2026):** publicados; `checar_endpoints` 272, 0 falhas. O publicado antes foi conferido igual ao git (só diferenças de formatação do Xano).
- [ ] 1.3 Rodar `tools/testar_treinamento_video_http.py` com login (RH ou Admin com ficha). Cobre também as validações do YouTube.

## 2. Frontend

- [x] 2.1 `drive_video.py`, `api_client.py` e `treinamentos_modelo.py` (D1, D3). Verificar: regras em `tools/testar_treinamentos.py`.
- [x] 2.2 Player (`video_player.py`, D4). Verificar: no Chrome, com um vídeo de teste servido localmente.
  - **Feito (21/10/2026):**
    - velocidade pedida em 4x ficou em 2x;
    - o salto para o fim voltou para o ponto já assistido;
    - o progresso foi enviado na pausa e no fim (100%, "Pronto: já pode concluir").
- [x] 2.3 Modal do RH e "Meus treinamentos" (D5). Verificar: `tools/testar_treinamentos.py`.
  - **Feito (21/10/2026):** 35/35, 12 verificações novas.
- [ ] 2.4 Configurar o Google Drive no app publicado e testar com um vídeo de verdade:
  - um projeto no Google Cloud com a Drive API ligada;
  - a chave de API restrita à Drive API e ao endereço do app;
  - a chave em `[google] drive_api_key` nos secrets do Streamlit.

## 4. YouTube como segunda fonte (pedido do usuário, 21/10/2026)

- [x] 4.1 `treinamento.video_fonte` e as validações do YouTube nas rotas (D6). Verificar: dry-run com só o `ADD_FIELD` e os 3 `UPDATE`.
  - **Feito (21/10/2026):** publicado; `checar_endpoints` 272, 0 falhas.
- [x] 4.2 Link do Drive ou do YouTube no mesmo campo, prévia do YouTube no modal e player do YouTube (D6). Verificar: `tools/testar_treinamentos.py` e no Chrome.
  - **Feito (21/10/2026):**
    - testes: 39/39;
    - no Chrome, a prévia leu a duração do vídeo de exemplo do YouTube (1344 s);
    - o salto para 120 s voltou para o ponto já assistido;
    - a velocidade ficou em 2x;
    - o progresso foi enviado na pausa;
    - o player do Drive, testado de novo, continua igual.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 21), `docs/lgpd/operadores.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`, `docs/deploy.md` e `.streamlit/secrets.toml.example`. Verificar: `openspec validate treinamento-em-video`.
