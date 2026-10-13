# Tasks

## 1. Figma

- [ ] 1.1 Modal "Enviar documento" (309:1591, escuro 313:1573) com o campo "Arquivo" no lugar de "Link do arquivo". Verificar: prints dos nós.
  - **Pendente (13/10/2026):** o MCP do Figma não conectou nesta sessão. O campo "Arquivo" era o do protótipo original (309:1591 passou a "Link do arquivo" na tarefa 62); volta a ele.

## 2. Backend

- [x] 2.1 `documentos/envio_arquivo` POST: checklist, perfil (próprio colaborador ativo, RH ou Admin), extensão PDF/JPG/JPEG/PNG, caminho UUID, endereço de envio do Supabase, auditoria. Verificar: `tools/checar_endpoints.py` sem falha; por HTTP, sem as variáveis devolve a mensagem de "não configurado".
  - **Feito (13/10/2026):** publicado; `checar_endpoints` 219, 0 falhas. Teste por HTTP: não verificado (precisa do código de acesso por e-mail e da configuração da 5.1).
- [x] 2.2 `documentos/{id}/arquivo` GET com link assinado de 5 minutos para arquivo do Supabase; links antigos sem mudança. Verificar: `tools/checar_endpoints.py`; por HTTP, depois da configuração (D7), abrir um arquivo anexado como dono e ter 403 como Gestor.
  - **Feito (13/10/2026):** publicado. Sem as variáveis do Supabase, o comportamento é o de antes. Teste por HTTP: não verificado (depende da 5.1).

## 3. Frontend

- [x] 3.1 Modal "Enviar documento" com "Arquivo" (PDF, JPG ou PNG, até 10 MB): pede o endereço, envia o arquivo e cadastra o documento. Verificar: `tools/testar_privacidade_documentos.py` com AppTest e API simulada.
  - **Feito (13/10/2026):** 86/86. O AppTest não simula o envio de arquivo; o teste troca o `st.file_uploader` por um arquivo fictício em memória.

## 4. Documentação e LGPD

- [x] 4.1 Supabase em `docs/lgpd/operadores.md` (antes do primeiro arquivo), R1.5 em `docs/lgpd/ripd.md`, pendência de apagar arquivos em `docs/lgpd/retencao.md`; `AGENTS.md`, `docs/arquitetura.md` e `docs/regras-de-negocio.md`. Verificar: descrevem D1 a D7.
  - **Feito (13/10/2026):** também `README.md` e `xano-workspace/AGENTS.md`.

## 5. Configuração (equipe)

- [ ] 5.1 Projeto no Supabase em São Paulo, bucket privado `documentos` (10 MB; PDF, JPEG e PNG) e as variáveis no Xano (D7). Verificar: envio e abertura de um arquivo de teste fictício, registrados em `docs/evidencias/`.
