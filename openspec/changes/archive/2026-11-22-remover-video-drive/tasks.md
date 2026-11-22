# Tasks

- [x] 1 Frontend:
  - modal do RH só com o YouTube;
  - aviso para o vídeo antigo do Drive;
  - remover `drive_video.py` e a seção `[google]` dos secrets.

  Verificar: `tools/testar_treinamentos.py`.
- [x] 2 Backend: POST e PATCH de `treinamentos` só aceitam vídeo do YouTube. Verificar: `checar_endpoints`, a paridade com o Xano e um teste das expressões.
- [x] 3 Documentação: `deploy.md`, `lgpd/operadores.md`, aviso de privacidade, regras de negócio (seção 21) e as documentações técnica e do usuário.

## Notas (22/11/2026)

- **1:** `tools/testar_treinamentos.py` passa 83 de 83. Cobre:
  - o link do Drive recusado no modal, com a orientação de usar o YouTube;
  - o vídeo antigo do Drive com o aviso, sem player;
  - o vídeo do YouTube tocando sem chave nenhuma.
- **2:** publicado no Xano, e o dry-run seguinte deu "No changes". `checar_endpoints` passa com 308 endpoints. A tabela só mudou no comentário: o enum segue com `drive` para os registros antigos.
- **3:** documentos atualizados. Na LGPD, a API do Drive passou para "retirado", e o Drive e o Slides continuam só como links de material de leitura.
