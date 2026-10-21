# Proposal

## Why

O usuário pediu (21/10/2026) que o RH possa publicar os treinamentos em vídeo pela plataforma, ligados ao Google Drive. Também pediu que o sistema meça se a pessoa assistiu e só libere "Concluir treinamento" quando o vídeo acabar.

Hoje o treinamento acontece fora e o RH registra a conclusão de cada turma (change `treinamentos-obrigatorios`). Para a orientação anual sobre assédio (Lei 14.457/2022) e para os treinamentos de integração, um vídeo resolve, e a prova de que a pessoa assistiu vira um registro do próprio sistema.

## What Changes

- **Vídeo no catálogo** (D1): o treinamento ganha o vídeo do Google Drive (o id do arquivo), a duração e o mínimo a assistir (95% por padrão). A duração é lida do Drive quando o RH salva.
- **Progresso** (D2): tabela `treinamento_progresso` e `meus_treinamentos/{id}/progresso` POST. O backend recusa progresso mais rápido que 2x o tempo real e nunca diminui o que foi gravado.
- **Conclusão pela pessoa** (D3): `meus_treinamentos/{id}/concluir` POST, só depois do mínimo assistido, com a validade calculada como no registro do RH. Depois, o progresso é zerado.
- **Player** (D4): componente do Streamlit com o vídeo direto do Drive. Conta o ponto mais longe assistido sem pular, limita a velocidade a 2x e grava o progresso.
- **Telas** (D5):
  - o modal do treinamento (RH) ganha o link do Drive e o mínimo;
  - "Meus treinamentos" ganha o player e "Concluir treinamento".

## Non-goals

- Upload do vídeo pelo ConectaRH: o arquivo fica no Drive da empresa, e o RH cola o link.
- YouTube, Vimeo e outros serviços: só o Google Drive, como pedido.
- Prova ou questionário depois do vídeo.
- Garantia de atenção: o sistema mede o tempo assistido, não se a pessoa prestou atenção. Uma aba tocando sozinha conta.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: treinamento com vídeo do Google Drive, progresso medido e conclusão pela própria pessoa depois do mínimo assistido.

## Impact

- **Backend:**
  - tabela nova `treinamento_progresso`;
  - campos novos em `treinamento`: `video_drive_id`, `video_duracao` e `video_percentual_minimo`;
  - endpoints novos: `meus_treinamentos/{id}/progresso` e `meus_treinamentos/{id}/concluir`;
  - alterados: `treinamentos` POST, `treinamentos/{id}` PATCH e `meus_treinamentos` GET.
- **Frontend:**
  - novos: `drive_video.py` e `video_player.py`;
  - alterados: `api_client.py`, `treinamentos_modelo.py`, `pagina_treinamentos.py` e `pagina_meus_treinamentos.py`.
- **Configuração:** chave de API do Google em `st.secrets["google"]["drive_api_key"]` (fora do repositório; exemplo em `.streamlit/secrets.toml.example`).
- **Figma:** "Meus treinamentos — assistir o vídeo" (557:1383) e "Modal/Novo treinamento — com vídeo" (557:1477), na seção 22.
- **Testes:**
  - `tools/testar_treinamentos.py`;
  - novo `tools/testar_treinamento_video_http.py`.
- **Documentação:**
  - `docs/regras-de-negocio.md` (seção 21);
  - `docs/lgpd/operadores.md` (Google como operador);
  - `docs/lgpd/registro-de-operacoes.md`;
  - `docs/figma-pendencias.md`;
  - `docs/deploy.md`.
