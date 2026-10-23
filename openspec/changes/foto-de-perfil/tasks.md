# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil. As evidências vão para `docs/evidencias/foto-de-perfil.md`, sem dado pessoal: só fotos de exemplo geradas para o teste, nunca de uma pessoa real.

## 1. Tela

- [ ] 1.1 Figma, desenhado antes de codar, nos temas claro e escuro. Verificar: print dos nós.
  - o bloco da foto em "Meu perfil": a foto ou as iniciais, "Enviar foto", "Trocar", "Remover" e as regras de formato;
  - o cartão de pessoa do organograma com a foto;
  - o avatar do topo com a foto;
  - o modal "Remover foto" do RH, com a justificativa.
- [ ] 1.2 O componente `avatar` em `theme.py` (foto ou iniciais) e o tratamento da imagem com o Pillow (D2, D5). Verificar: regras em `tools/testar_perfil.py`. Uma foto 4000 × 3000 com EXIF vira 256 × 256 WebP sem EXIF; um PDF é recusado.
- [ ] 1.3 "Meu perfil" com o bloco da foto, com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada) (D3). Verificar: `tools/testar_perfil.py`.
- [ ] 1.4 O organograma e o topo com a foto, e a ficha do colaborador com "Remover foto" para o RH (D4, D5). Verificar: `tools/testar_organograma.py` e `tools/testar_cadastro.py`.

## 2. Integrar

- [ ] 2.1 O bucket privado `fotos-perfil` no Supabase e o campo `colaborador.foto_path` (D1). Verificar: dry-run só com `ADD_FIELD`, e o bucket sem acesso público (uma URL sem assinatura dá 400 ou 404).
- [ ] 2.2 `minha_foto/envio`, `minha_foto` POST e DELETE, com a guarda e a auditoria (D3). Verificar: `checar_endpoints` e a 3.1.
- [ ] 2.3 `colaboradores/{id}/foto` DELETE, só RH e Admin, com justificativa, auditoria e aviso (D4). Verificar: a 3.2.
- [ ] 2.4 `foto_url` assinada em `meu_perfil_colaborador` GET, `auth/me` e `organograma` GET, com assinatura em lote (D5). Verificar: o `output` do organograma continua só com id, nome, cargo, departamento, superior e `foto_url`.

## 3. Testar

- [ ] 3.1 HTTP, a própria pessoa:
  - **passa:** envia e a foto aparece no perfil e no organograma visto por outro usuário; depois de remover, a `foto_url` some;
  - **falha:** um caminho fora do padrão dá 400, e gravar a foto de outra pessoa não é possível (403).
- [ ] 3.2 HTTP, RH e Admin:
  - **passa:** removem com justificativa (com auditoria e aviso);
  - **falha:** sem justificativa dá 400, e o Colaborador e o Gestor recebem 403.
- [ ] 3.3 HTTP, expiração: a URL assinada abre agora e, com a validade mínima de teste, não abre depois.
- [ ] 3.4 LGPD e regras, depois da implementação: `docs/lgpd/registro-de-operacoes.md`, `docs/lgpd/operadores.md`, `docs/lgpd/retencao.md`, o aviso de privacidade e `docs/regras-de-negocio.md`. Verificar: `openspec validate foto-de-perfil`.
