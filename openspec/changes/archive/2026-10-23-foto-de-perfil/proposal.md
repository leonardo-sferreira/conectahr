# Proposal

## Why

Mapeamento de Leonardo (23/10/2026). Hoje o perfil e o organograma mostram só as iniciais. Ver o rosto dos colegas ajuda a reconhecer quem é quem, principalmente no organograma, que é por onde a pessoa conhece a estrutura da empresa.

## What Changes

- **A própria pessoa** envia, troca e remove a foto em "Meu perfil" (D3).
- **Onde a foto aparece** (D5):
  - no perfil;
  - no organograma, em cada pessoa, com nome, cargo e setor;
  - no avatar do topo.
  - Sem foto, aparecem as iniciais, como hoje.
- **RH e Admin** removem uma foto inadequada, com justificativa e auditoria (D4).
- **Armazenamento** (D1, D2): bucket privado `fotos-perfil` no Supabase Storage, como na change `anexo-de-arquivos`. O campo `colaborador.foto_path` guarda o caminho, nunca a URL. As URLs são assinadas e de curta duração, geradas pelo backend.

## Non-goals

- **Reconhecimento facial**, ou qualquer uso da foto além de mostrar. É o que mantém a foto fora do dado sensível (biométrico).
- **Foto obrigatória:** ninguém precisa ter (D6).
- **Recorte manual na tela:** o recorte é automático, centralizado.
- **Foto de quem não tem ficha de colaborador.**

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: foto de perfil opcional, mostrada no perfil, no organograma e no topo.

## Impact

- **Backend:**
  - campo `colaborador.foto_path`;
  - endpoints novos: `minha_foto/envio` POST, `minha_foto` POST e DELETE, e `colaboradores/{id}/foto` DELETE;
  - alterados: `meu_perfil_colaborador` GET, `organograma` GET e `auth/me` (a URL do avatar).
- **Supabase:** o bucket privado `fotos-perfil`.
- **Frontend:**
  - `api_client.py`;
  - `pagina_perfil.py` (o bloco da foto);
  - `pagina_organograma.py` e `organograma_modelo.py` (a pessoa com foto);
  - `theme.py` (avatar com foto ou iniciais, e o topo);
  - a ficha do colaborador (RH: remover).
- **Figma:** o bloco da foto em "Meu perfil" (a partir de 224:3593 e do perfil), o cartão de pessoa do organograma com foto e o avatar do topo com foto, nos temas claro e escuro.
- **Testes:** `tools/testar_perfil.py`, `tools/testar_organograma.py` e o novo `tools/testar_foto_perfil_http.py`.
- **LGPD:**
  - `docs/lgpd/registro-de-operacoes.md` (finalidade da foto e cobertura);
  - `docs/lgpd/operadores.md` (Supabase recebe a foto);
  - `docs/lgpd/retencao.md`;
  - aviso de privacidade.
