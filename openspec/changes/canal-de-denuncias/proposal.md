# Proposal

## Why

O usuário pediu (20/10/2026) a prioridade 1 da pesquisa de mercado: funções que a lei exige. A Lei 14.457/2022 obriga as empresas com CIPA (mais de 20 empregados) a ter um canal de denúncias de assédio e violência no trabalho que:
- garanta o anonimato;
- permita acompanhar a denúncia;
- leve a uma apuração formal.

O ConectaRH não tem nada disso, e os sistemas de RH concorrentes também costumam não trazer.

## What Changes

- **Dados** (D1): tabelas `denuncia` e `denuncia_mensagem`, sem vínculo com conta e sem horário. O código de acompanhamento é guardado só como hash.
- **Comissão de ética** (D2): tabela `comissao_etica`. Só os membros veem as denúncias; o Admin escolhe quem é membro.
- **Canal público** (D3):
  - enviar, acompanhar pelo código e responder, sem login (também pelo link da tela Entrar);
  - o código aparece uma única vez.
- **Apuração** (D4): fila, detalhe (cada abertura auditada), mensagem ao denunciante e conclusão com o resultado e o parecer.
- **Membros e menu** (D5):
  - o Admin inclui e remove membros em "Usuários e perfis";
  - `auth/me` diz se a conta é membro, para o menu mostrar "Denúncias".
- **Telas** (D6): "Canal de denúncias" (todos e público), "Denúncias" (comissão) e o cartão "Comissão de ética".

## Non-goals

- Anexar arquivos à denúncia.
- Canal por telefone ou por e-mail externo.
- Encaminhar a denúncia a um serviço externo de ouvidoria.
- Impedimento automático de um membro citado na denúncia: a comissão decide; fica registrado como risco no RIPD.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: canal de denúncias anônimo, com acompanhamento pelo código e apuração pela comissão de ética.

## Impact

- **Backend:**
  - tabelas novas: `denuncia`, `denuncia_mensagem` e `comissao_etica`;
  - endpoints novos: `denuncias` POST e GET, `denuncias/acompanhar`, `denuncias/responder`, `denuncias/{id}` GET, `denuncias/{id}/mensagem`, `denuncias/{id}/concluir`, `minha_comissao_etica`, `comissao_etica` GET e POST e `comissao_etica/{id}/remover`;
  - endpoint alterado: `auth/me`.
- **Frontend:** `api_client.py`, `denuncias_modelo.py`, `pagina_canal_denuncias.py`, `pagina_denuncias.py`, `comissao_etica_ui.py`, `pagina_usuarios.py`, `pagina_entrar.py`, `app.py` e `theme.py`.
- **Figma:** seção 20 (540:1194).
- **Testes:** `tools/testar_denuncias.py` e o `tools/testar_cadastro.py` (cartão da comissão).
- **Documentação:**
  - `docs/regras-de-negocio.md` (seção 19);
  - `docs/lgpd/registro-de-operacoes.md` (F20), `retencao.md` e `ripd.md` (seção 4);
  - `docs/figma-pendencias.md`.
