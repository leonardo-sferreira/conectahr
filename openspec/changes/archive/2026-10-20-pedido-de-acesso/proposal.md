# Proposal

## Why

O tipo de acesso (perfil) de uma conta só podia ser escolhido pelo Admin, na criação da conta ou em Usuários e perfis. Na admissão e na ficha do colaborador não havia como definir nem pedir outro perfil, e o RH não tinha um caminho formal para pedir ao Admin a liberação de Gestor, RH ou Admin. O usuário pediu (14/10/2026) que só o Admin altere o acesso, direto pelo cadastro do colaborador, e que o RH abra um pedido, dizendo qual acesso quer, para o Admin aprovar ou recusar.

## What Changes

- **Tabela `solicitacao_acesso`** e quatro endpoints em Gestão de Usuários: `solicitacoes_acesso` POST (RH pede, com justificativa), GET (RH e Admin), `solicitacoes_acesso/{id}/aprovar` e `/recusar` (só Admin) (D1 e D2).
- **Admissão:** o RH escolhe o tipo de acesso, que o "Criar acesso" seguinte traz marcado.
- **Criar acesso:** o RH também escolhe; perfil diferente de Colaborador cria a conta como Colaborador e manda o pedido ao Admin. O Admin continua criando já com o perfil.
- **Ficha do colaborador:** mostra o tipo de acesso e o pedido pendente; "Alterar acesso" para o Admin (troca na hora) e "Solicitar alteração de acesso" para o RH.
- **Usuários e perfis:** os pedidos pendentes, com Aprovar e Recusar (com motivo), e o histórico.

## Non-goals

- Mudar quem troca o perfil direto: continua só o Admin (`usuarios/{id}/perfil`).
- Prazo ou expiração do pedido.
- Pedido feito pelo Gestor ou pelo próprio colaborador.

## Impact

- Backend: `table/solicitacao_acesso.xs`; `api/conecta_rh_gestao_de_usuarios/solicitacoes_acesso_POST.xs`, `solicitacoes_acesso_GET.xs`, `solicitacoes_acesso/id/aprovar_POST.xs` e `recusar_POST.xs`.
- Frontend: `api_client`, `cadastro_modelo`, `pagina_colaboradores.py`, `pagina_usuarios.py`.
- Documentação: `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`.
