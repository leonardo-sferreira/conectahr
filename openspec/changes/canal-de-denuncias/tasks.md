# Tasks

## 0. Figma

- [x] 0.1 Desenhar a seção 20 (540:1194): canal, modais "Denúncia enviada" e "Acompanhar denúncia", fila da comissão, modais "Denúncia" e "Concluir apuração" e o cartão "Comissão de ética" (D6). Verificar: prints dos nós.
  - **Feito (20/10/2026):** modo claro. Falta a versão escura (docs/figma-pendencias.md).

## 1. Backend

- [x] 1.1 Tabelas `denuncia`, `denuncia_mensagem` e `comissao_etica` (D1, D2). Verificar: dry-run só com `CREATE`.
  - **Feito (20/10/2026):** publicadas.
- [x] 1.2 Endpoints públicos `denuncias` POST, `denuncias/acompanhar` e `denuncias/responder` (D3). Verificar: por HTTP, um caso que passa e um que falha.
  - **Feito (20/10/2026):** publicados e testados por HTTP sem login. Recusas: tipo inválido 400, relato curto 400, código curto 400, código inexistente 404 (acompanhar e responder). Caminho completo: enviou a denúncia de teste DEN-1 (código de 16 sinais), acompanhou com o código em minúsculas e sem hífens, respondeu e viu a mensagem com só a data; a resposta não traz a identificação.
- [x] 1.3 Endpoints da comissão e dos membros, e `auth/me` com `membro_comissao_etica` (D4, D5). Verificar: `checar_endpoints`, sem token 401, e `auth/me` conferido igual ao git antes.
  - **Feito (20/10/2026):** publicados; `checar_endpoints` 262, 0 falhas.
- [ ] 1.4 Testar com login de verdade: Admin inclui um membro; o membro vê "Denúncias", abre a DEN-1, escreve e conclui como "inconclusiva"; quem não é membro (inclusive RH e Admin) recebe 403.

## 2. Frontend

- [x] 2.1 `api_client.py` e `denuncias_modelo.py`. Verificar: regras em `tools/testar_denuncias.py`.
- [x] 2.2 "Canal de denúncias" (logado e público) e o link na tela Entrar (D6). Verificar: `tools/testar_denuncias.py`.
- [x] 2.3 "Denúncias" da comissão e o item do menu só para membros (D6). Verificar: idem.
  - **Feito (20/10/2026):** 27/27.
- [x] 2.4 Cartão "Comissão de ética" em "Usuários e perfis" (D5). Verificar: `tools/testar_cadastro.py`.
  - **Feito (20/10/2026):** 110/110.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 19), LGPD (registro F20, retenção e RIPD seção 4) e `docs/figma-pendencias.md`. Verificar: `openspec validate canal-de-denuncias`.
- [ ] 3.2 Acrescentar a finalidade F20 ao aviso de privacidade (documento e as cópias no Figma, que precisam continuar idênticos).
