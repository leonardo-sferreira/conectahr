# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil. As evidências vão para `docs/evidencias/foto-de-perfil.md`, sem dado pessoal: só fotos de exemplo geradas para o teste, nunca de uma pessoa real.

## 1. Tela

- [x] 1.1 Figma, desenhado antes de codar. Verificar: print dos nós.
  - **Feito (23/10/2026):** seção 25 (571:870): o Perfil com o cartão da foto (571:1042) e a foto no topo, o organograma com fotos e iniciais (571:1068) e o modal do RH (571:1179). Só no modo claro; falta a versão escura.
  - o bloco da foto em "Meu perfil": a foto ou as iniciais, "Enviar foto", "Trocar", "Remover" e as regras de formato;
  - o cartão de pessoa do organograma com a foto;
  - o avatar do topo com a foto;
  - o modal "Remover foto" do RH, com a justificativa.
- [x] 1.2 O componente `avatar` em `theme.py` (foto ou iniciais) e o tratamento da imagem com o Pillow (D2, D5). Verificar: regras em `tools/testar_perfil.py`. Uma foto 4000 × 3000 com EXIF vira 256 × 256 WebP sem EXIF; um PDF é recusado.
- [x] 1.3 "Meu perfil" com o bloco da foto, com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada) (D3). Verificar: `tools/testar_perfil.py`.
- [x] 1.4 O organograma e o topo com a foto, e a ficha do colaborador com "Remover foto" para o RH (D4, D5). Verificar: `tools/testar_organograma.py` e `tools/testar_cadastro.py`.

## 2. Integrar

- [x] 2.1 O bucket privado `fotos-perfil` no Supabase e o campo `colaborador.foto_path` (D1). Verificar: dry-run só com `ADD_FIELD`, e o bucket sem acesso público (uma URL sem assinatura dá 400 ou 404).
- [x] 2.2 `minha_foto/envio`, `minha_foto` POST e DELETE, com a guarda e a auditoria (D3). Verificar: `checar_endpoints` e a 3.1.
- [x] 2.3 `colaboradores/{id}/foto` DELETE, só RH e Admin, com justificativa, auditoria e aviso (D4). Verificar: a 3.2.
- [x] 2.4 `foto_url` assinada em `meu_perfil_colaborador` GET, `auth/me` e `organograma` GET, com assinatura em lote (D5). Verificar: o `output` do organograma continua só com id, nome, cargo, departamento, superior e `foto_url`.
  - **Feito (23/10/2026), 1.2 a 2.4:**
    - backend publicado (o que estava no ar foi conferido igual ao `master` antes); `checar_endpoints` 280, 0 falhas;
    - testes: `testar_perfil` 72/72 (com o tratamento da imagem: 4000 × 3000 com EXIF vira 256 × 256 WebP sem EXIF), `testar_organograma` 34/34 e `testar_cadastro`;
    - no Chrome, com dados simulados: Perfil, menu da conta e organograma (com foto e com iniciais), nos dois temas;
    - junto: a anonimização do desligado apaga a foto (D6).

## 3. Testar

As três primeiras rodam em `tools/testar_foto_perfil_http.py`, com a conta que envia e, opcional, uma do RH ou Admin. A foto do teste é uma imagem de cor sólida, sem dado pessoal.


- [ ] 3.1 HTTP, a própria pessoa:
  - **passa:** envia e a foto aparece no perfil e no organograma visto por outro usuário; depois de remover, a `foto_url` some;
  - **falha:** um caminho fora do padrão dá 400, e gravar a foto de outra pessoa não é possível (403).
- [ ] 3.2 HTTP, RH e Admin:
  - **passa:** removem com justificativa (com auditoria e aviso);
  - **falha:** sem justificativa dá 400, e o Colaborador e o Gestor recebem 403.
- [ ] 3.3 HTTP, expiração: a URL assinada abre agora e, com a validade mínima de teste, não abre depois.
- [x] 3.4 LGPD e regras, depois da implementação: `docs/lgpd/registro-de-operacoes.md`, `docs/lgpd/operadores.md`, `docs/lgpd/retencao.md`, o aviso de privacidade e `docs/regras-de-negocio.md`. Verificar: `openspec validate foto-de-perfil`.
  - **Feito (23/10/2026).**
